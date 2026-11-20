"""Inactive source doors must not deadlock the route (34060 stage1/2)."""
import sys, unittest, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from els_server.domain.dungeon_routes import DungeonRun

def ready(run,now,kill=True):
    if kill:
        for n in run.current['npcs']:
            if n['active'] and n.get('team',1)!=0:run.defeated[n['key']]=b'd'
    run.portal_requested=True;run.loaded()
    for _ in range(20):
        if run.poll_ready():return True
        now[0]+=1
    return False

class GateConditionTests(unittest.TestCase):
    def run_to(self,stage,part,kill=True):
        now=[0.0];run=DungeonRun(34060,str(uuid.uuid4()),clock=lambda:now[0])
        for _ in range(12):
            if (run.stage,run.part)==(stage,part):
                if kill:self.assertTrue(ready(run,now))
                else:ready(run,now,False)
                return run
            self.assertTrue(ready(run,now))
            self.assertNotEqual(run.advance(),'clear')
        self.fail('route did not reach target part')

    def test_inactive_door_opens_after_active_mobs(self):
        run=self.run_to(1,0)
        door=next(n for n in run.current['npcs'] if n['template']==6212)
        self.assertNotIn(door['key'],run.defeated)
        self.assertTrue(run.poll_ready())

    def test_stage_two_door_opens_after_mobs(self):
        run=self.run_to(2,1)
        door=next(n for n in run.current['npcs'] if n['template']==6213)
        self.assertNotIn(door['key'],run.defeated)
        self.assertTrue(run.poll_ready())

    def test_live_boss_still_required(self):
        run=self.run_to(3,0,kill=False)
        self.assertFalse(run.poll_ready())

    def test_summon_controllers_do_not_block_the_door(self):
        run=self.run_to(1,0,kill=False)
        self.assertTrue(run.poll_ready())

    def test_route_reaches_clear(self):
        now=[0.0];run=DungeonRun(34060,str(uuid.uuid4()),clock=lambda:now[0])
        for _ in range(12):
            self.assertTrue(ready(run,now))
            if run.advance()=='clear':return
        self.fail('route never cleared')

if __name__=='__main__':
    unittest.main()
