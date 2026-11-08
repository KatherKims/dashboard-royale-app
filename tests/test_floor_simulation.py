import copy
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.data_bundle import load_bundle
from dashboard.floor_simulation import FloorSimulation

class FloorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=FloorSimulation(load_bundle())
        cls.m,cls.n,cls.p=sorted(cls.sim.eligible)[:3]
        cls.slot=sorted(set(cls.sim.slots.index)-set(cls.sim.initial))[0]
    def move(self): return dict(id='move1',kind='move',target=self.m,destination=self.slot)
    def test_catalog_reconciliation_and_timing(self):
        for kind,aid,target in [('move','A-MOVE-MACHINE',self.m),('lease','A-REPLACE-LEASE',self.m),
                                ('inspect','A-INSPECT',self.m),('maintenance','A-PREVENTIVE','Ridgeline')]:
            a=dict(id='a',kind=kind,target=target)
            if kind=='move': a['destination']=self.slot
            r=self.sim.evaluate([a]); e=self.sim.engine.evaluate(aid,target)
            np.testing.assert_allclose(r['_net'],e['net'],atol=1e-9)
            self.assertAlmostEqual(r['cash_committed'],e['cost'])
            self.assertEqual(r['days'][0]['daily_cash'],self.sim.engine.catalog[aid]['unit_cost_cents']/100)
            if kind=='lease':
                self.assertEqual(r['days'][13]['daily_cash'],0)
                self.assertEqual(r['days'][14]['daily_cash'],55)
            s=r['summary']
            self.assertAlmostEqual(s['expected_gaming_earnings']-s['baseline']-s['cash_paid'],s['mean'],places=7)
    def test_swap_atomic_and_undo(self):
        a=dict(id='swap',kind='swap',target=self.m,other=self.n)
        r=self.sim.evaluate([a]);sm=self.sim.original_slot[self.m];sn=self.sim.original_slot[self.n]
        self.assertEqual(r['cash_committed'],3600)
        self.assertEqual(r['days'][1]['layout'][sm],self.m)
        self.assertEqual(r['days'][2]['layout'][sm],self.n)
        self.assertEqual(r['days'][2]['layout'][sn],self.m)
        self.assertEqual(r['configurations'][self.m],self.sim.slots.loc[sm,'config_id'])
        self.assertEqual(r['configurations'][self.n],self.sim.slots.loc[sn,'config_id'])
        self.assertTrue(all(d['machine_count']==308 for d in r['days']))
        e=self.sim.engine.evaluate('A-MOVE-MACHINE',self.m)['net']+self.sim.engine.evaluate('A-MOVE-MACHINE',self.n)['net']
        np.testing.assert_allclose(r['_net'],e)
        self.assertEqual(self.sim.undo(r['plan'],'swap')['summary']['layout'],self.sim.initial)
    def test_preview_is_pure_and_confirmation_bound(self):
        plan=[];action=self.move();before=copy.deepcopy(action)
        r=self.sim.preview(plan,action)
        self.assertEqual(plan,[]);self.assertEqual(action,before)
        np.testing.assert_allclose(r['_net'],self.sim.confirm(plan,action,r['estimate_id'])['_net'])
        altered={**action,'target':self.n}
        with self.assertRaises(ValueError):self.sim.confirm(plan,altered,r['estimate_id'])
    def test_invalid_inputs(self):
        for x in [None,{},'hi',[None],[{**self.move(),'cash':0}], [{**self.move(),'id':'<img>'}],
                  [{**self.move(),'target':'NEW-x'}], [{**self.move(),'retained':float('nan')}],
                  [{**self.move(),'retained':True}], [{**self.move(),'destination':'not-a-slot'}]]:
            with self.subTest(x=x),self.assertRaises(ValueError): self.sim.evaluate(x)
    def test_reserved_overlap_occupied_and_chain(self):
        a=self.move()
        for b in [dict(id='b',kind='move',target=self.n,destination=self.slot),
                  dict(id='b',kind='inspect',target=self.m),
                  dict(id='b',kind='move',target=self.n,destination=self.sim.original_slot[self.m])]:
            with self.assertRaises(ValueError):self.sim.evaluate([a,b])
        with self.assertRaises(ValueError):self.sim.evaluate([{**a,'destination':self.sim.original_slot[self.n]}])
    def test_remove_add_dependencies(self):
        remove=dict(id='remove',kind='remove',target=self.m,cash=100,day=3,share=.5)
        add=dict(id='add',kind='add',proxy=self.n,destination=self.sim.original_slot[self.m],cash=200,day=3,share=.5)
        r=self.sim.evaluate([remove,add])
        self.assertEqual(r['days'][1]['layout'][add['destination']],self.m)
        self.assertEqual(r['days'][2]['layout'][add['destination']],'NEW-add')
        self.assertEqual(r['days'][0]['cash_paid'],300)
        self.assertEqual(r['summary']['machine_count'],308)
        with self.assertRaises(ValueError):self.sim.undo(r['plan'],'remove')
        self.assertEqual(len(self.sim.undo(r['plan'],'add')['plan']),1)
        with self.assertRaises(ValueError):self.sim.evaluate([{**remove,'day':4},add])
    def test_extension_math(self):
        a=dict(id='x',kind='remove',target=self.m,cash=100,day=10,share=1)
        r=self.sim.evaluate([a]);np.testing.assert_allclose(r['_net'],-100)
        r=self.sim.evaluate([{**a,'share':0}])
        expected=-self.sim.forecast[self.m].iloc[9:].sum()*self.sim.engine.demand-100
        np.testing.assert_allclose(r['_net'],expected)
        for key,value in [('day',0),('day',3.5),('share',1.1),('cash',-1),('cash',True)]:
            with self.assertRaises(ValueError):self.sim.evaluate([{**a,key:value}])
    def test_budget_types_quantities(self):
        a=dict(id='x',kind='add',proxy=self.m,destination=self.slot,cash=100000,day=1,share=.5)
        self.assertEqual(self.sim.evaluate([a])['remaining_budget'],0)
        with self.assertRaises(ValueError):self.sim.evaluate([a,dict(id='i',kind='inspect',target=self.n)])
        ms=sorted(self.sim.eligible)
        swaps=[dict(id=f's{i}',kind='swap',target=ms[2*i],other=ms[2*i+1]) for i in range(13)]
        self.assertEqual(self.sim.evaluate(swaps[:12])['cash_committed'],43200)
        with self.assertRaises(ValueError):self.sim.evaluate(swaps)
        plan=[self.move(),dict(id='i',kind='inspect',target=self.n),dict(id='l',kind='lease',target=self.p),
              dict(id='r',kind='remove',target=ms[4],cash=0,day=1,share=.5)]
        with self.assertRaises(ValueError):self.sim.evaluate(plan)
    def test_suggestions_deterministic_marginal_and_conflicts(self):
        plan=[dict(id='i',kind='inspect',target=self.m)];before=copy.deepcopy(plan)
        a=self.sim.suggestions(plan);b=self.sim.suggestions(plan)
        self.assertEqual(a,b);self.assertEqual(plan,before)
        means=[x['marginal']['mean'] for x in a['suggestions']]
        self.assertEqual(means,sorted(means,reverse=True))
        for suggestion in a['suggestions']:
            self.assertNotEqual(suggestion['action']['target'],self.m)
            preview=self.sim.preview(plan,suggestion['action'])
            self.assertAlmostEqual(preview['marginal']['mean'],suggestion['marginal']['mean'])
        exhausted=[dict(id='a',kind='add',proxy=self.m,destination=self.slot,cash=100000,day=1,share=.5)]
        self.assertEqual(self.sim.suggestions(exhausted)['suggestions'],[])

if __name__=='__main__':unittest.main()
