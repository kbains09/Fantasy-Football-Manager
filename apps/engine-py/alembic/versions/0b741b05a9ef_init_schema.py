"""init schema

Revision ID: 0b741b05a9ef
Revises: dde58d8d1346
Create Date: 2025-09-04 18:31:49.154828
"""
from typing import Sequence, Union

from alembic import op, context
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0b741b05a9ef"
down_revision: Union[str, Sequence[str], None] = "dde58d8d1346"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- New tables ---
    op.create_table(
        "leagues",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", "year"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("league_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Players: add columns as NULLable, backfill, then tighten ---
    with op.batch_alter_table("players") as b:
        b.add_column(sa.Column("ext_id", sa.String(), nullable=True))
        b.add_column(sa.Column("name", sa.String(), nullable=True))
        b.add_column(sa.Column("team", sa.String(), nullable=True))
        b.add_column(sa.Column("bye_week", sa.Integer(), nullable=True))

    # Backfill to satisfy NOT NULL constraints safely
    op.execute("UPDATE players SET name = COALESCE(name, ext_id, id)")
    op.execute("UPDATE players SET team = COALESCE(team, 'FA')")
    op.execute("UPDATE players SET pos  = COALESCE(pos,  'WR')")

    with op.batch_alter_table("players") as b:
        b.alter_column("name", existing_type=sa.String(), nullable=False)
        b.alter_column("team", existing_type=sa.String(), nullable=False)
        b.alter_column("pos", existing_type=sa.String(), nullable=False)

    # --- Teams: add season + league linkage (nullable), backfill via -x, then enforce ---
    with op.batch_alter_table("teams") as b:
        b.add_column(sa.Column("league_id", sa.Integer(), nullable=True))
        b.add_column(sa.Column("year", sa.Integer(), nullable=True))
        b.add_column(sa.Column("owner_ids", sa.JSON(), nullable=True))
        # Drop legacy if present
        try:
            b.drop_column("manager")
        except Exception:
            pass

    # Backfill from CLI args (preferred). Example:
    # poetry run alembic -x league_id=432155457 -x year=2025 upgrade head
    xargs = context.get_x_argument(as_dictionary=True)
    li = xargs.get("league_id")
    yr = xargs.get("year")
    if li and yr:
        op.execute(
            f"UPDATE teams SET league_id = {int(li)}, year = {int(yr)} "
            "WHERE league_id IS NULL OR year IS NULL"
        )
    else:
        # fallback: use newest leagues row if exists
        op.execute("""
            UPDATE teams t
            SET league_id = l.id, year = l.year
            FROM (SELECT id, year FROM leagues ORDER BY year DESC LIMIT 1) l
            WHERE (t.league_id IS NULL OR t.year IS NULL)
        """)

    with op.batch_alter_table("teams") as b:
        b.alter_column("league_id", existing_type=sa.Integer(), nullable=False)
        b.alter_column("year", existing_type=sa.Integer(), nullable=False)

    op.create_index("ix_team_league_year", "teams", ["league_id", "year"], unique=False)

    # --- Valuations: add metrics, create surrogate id with sequence, set PK ---
    # Add metric columns as nullable, then backfill to 0.0, then make NOT NULL.
    with op.batch_alter_table("valuations") as b:
        b.add_column(sa.Column("projected_points", sa.Float(), nullable=True))
        b.add_column(sa.Column("vorp", sa.Float(), nullable=True))

    op.execute("UPDATE valuations SET projected_points = COALESCE(projected_points, 0.0)")
    op.execute("UPDATE valuations SET vorp = COALESCE(vorp, 0.0)")

    with op.batch_alter_table("valuations") as b:
        b.alter_column("projected_points", existing_type=sa.Float(), nullable=False)
        b.alter_column("vorp", existing_type=sa.Float(), nullable=False)

    # Create sequence, add id with default nextval so existing rows get values,
    # then drop default (keep identity via sequence for inserts).
    op.execute("CREATE SEQUENCE IF NOT EXISTS valuations_id_seq")
    with op.batch_alter_table("valuations") as b:
        b.add_column(
            sa.Column(
                "id",
                sa.Integer(),
                server_default=sa.text("nextval('valuations_id_seq')"),
                nullable=False,
            )
        )
    # Remove default to avoid hard-coding it at ORM level; sequence still exists.
    with op.batch_alter_table("valuations") as b:
        b.alter_column("id", server_default=None)

    # Own the sequence (best-effort)
    try:
        op.execute("ALTER SEQUENCE valuations_id_seq OWNED BY valuations.id")
    except Exception:
        pass

    # Replace old unique if present, add new unique + FK + index.
    try:
        op.drop_constraint(op.f("uq_val_source_week"), "valuations", type_="unique")
    except Exception:
        pass

    op.create_index("ix_val_week", "valuations", ["week"], unique=False)
    # Keep unique so (player_id, week, source) stays deduped for upserts
    op.create_unique_constraint("uq_val_player_week_source", "valuations", ["player_id", "week", "source"])
    # Ensure FK exists
    try:
        op.create_foreign_key(None, "valuations", "players", ["player_id"], ["id"], ondelete="CASCADE")
    except Exception:
        pass

    # Switch primary key to id (drop old PK if any)
    try:
        op.drop_constraint("valuations_pkey", "valuations", type_="primary")
    except Exception:
        pass
    op.create_primary_key("valuations_pkey", "valuations", ["id"])

    # Remove old 'value' column if it existed
    try:
        with op.batch_alter_table("valuations") as b:
            b.drop_column("value")
    except Exception:
        pass

    # --- Rosters -> Roster Spots migration ---
    # Drop old 'rosters' table if present, then create roster_spots + index
    try:
        op.drop_table("rosters")
    except Exception:
        pass

    op.create_table(
        "roster_spots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("slot", sa.String(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "player_id", "week", name="uq_roster_entry"),
    )
    op.create_index("ix_roster_team_week", "roster_spots", ["team_id", "week"], unique=False)


def downgrade() -> None:
    """Best-effort downgrade."""
    # roster_spots -> rosters
    op.drop_index("ix_roster_team_week", table_name="roster_spots")
    op.drop_table("roster_spots")
    op.create_table(
        "rosters",
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("slot", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("team_id", "player_id", name=op.f("rosters_pkey")),
    )

    # valuations
    try:
        op.drop_constraint("valuations_pkey", "valuations", type_="primary")
    except Exception:
        pass
    try:
        op.drop_constraint("uq_val_player_week_source", "valuations", type_="unique")
    except Exception:
        pass
    try:
        op.drop_index("ix_val_week", table_name="valuations")
    except Exception:
        pass
    with op.batch_alter_table("valuations") as b:
        b.add_column(sa.Column("value", sa.Float(), nullable=False))
        b.drop_column("id")
        b.drop_column("vorp")
        b.drop_column("projected_points")
    try:
        op.execute("DROP SEQUENCE IF EXISTS valuations_id_seq")
    except Exception:
        pass

    # teams
    op.drop_index("ix_team_league_year", table_name="teams")
    with op.batch_alter_table("teams") as b:
        b.drop_column("owner_ids")
        b.drop_column("year")
        b.drop_column("league_id")
        # optional reverse:
        # b.add_column(sa.Column("manager", sa.String(), nullable=True))

    # players
    with op.batch_alter_table("players") as b:
        b.alter_column("pos", existing_type=sa.String(), nullable=True)
        b.drop_column("bye_week")
        b.drop_column("team")
        b.drop_column("name")
        b.drop_column("ext_id")

    # new tables
    op.drop_table("transactions")
    op.drop_table("leagues")
