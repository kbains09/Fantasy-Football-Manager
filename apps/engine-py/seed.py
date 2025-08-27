from db import SessionLocal
from models import Team, Player, Roster, Valuation

db = SessionLocal()
# teams
db.merge(Team(id="alpha", name="Alpha", manager="You"))
db.merge(Team(id="beta", name="Beta", manager="Rival"))

# roster for alpha (so these **won’t** be free agents)
db.merge(Player(id="rb_alpha1", pos="RB"))
db.merge(Roster(team_id="alpha", player_id="rb_alpha1", slot="RB1"))

# candidates as free agents (no roster rows)
for pid, pos, val in [
    ("wr_keenan_allen", "WR", 12.4),
    ("rb_jaylen_warren", "RB", 8.7),
    ("te_sam_laporta", "TE", 7.9),
]:
    db.merge(Player(id=pid, pos=pos))
    db.merge(Valuation(player_id=pid, value=val, source="baseline", week=0))
db.commit()
print("seeded")
