#!/usr/local/bin/python

import unittest

import dice

class TestDice(unittest.TestCase):
    def testParse(self):
        self.assertEqual(dice.parse('10'), ([], 10))
        self.assertEqual(dice.parse('d6'), ([6,], 0))
        self.assertEqual(dice.parse('4d6'), ([6,6,6,6], 0))
        self.assertEqual(dice.parse('4d6+10'), ([6,6,6,6], 10))
        self.assertEqual(dice.parse('4d6+d8'), ([6,6,6,6,8], 0))
        self.assertEqual(dice.parse('4d6+d8+12'), ([6,6,6,6,8], 12))
        self.assertEqual(dice.parse('4d6+d8+12+2'), ([6,6,6,6,8], 14))
        self.assertEqual(dice.parse('4d6-d8+12-2'), ([6,6,6,6,-8], 10))
        self.assertEqual(dice.parse('4d16-d8+12-2'), ([16,16,16,16,-8], 10))
        self.assertEqual(dice.parse('4d16-10d8+12-2'), ([16,16,16,16,-8,-8,-8,-8,-8,-8,-8,-8,-8,-8], 10))
        self.assertEqual(dice.parse('(2+2)d6'), ([6,6,6,6], 0))
        self.assertEqual(dice.parse('(2+2)d6+(3-2d2)'), ([6,6,6,6,-2,-2], 3))
        self.assertRaises(ValueError, dice.parse, '4d(2d3)')

    def testCanonical(self):
        self.assertEqual(dice.canonical(([], 10)), '10')
        self.assertEqual(dice.canonical(([6,6], 10)), '2d6+10')

    def testRoll(self):
        for i in xrange(100):
            self.failUnless(0 < dice.roll('d6') < 7)
            self.failUnless(10 < dice.roll('d6 + 10') < 17)
            self.failUnless(-10 < dice.roll('d6 - d10') < 6)
    
    def testMetaRoll(self):
        self.assertEqual(dice.max_roll('d6'), 6)
        self.assertEqual(dice.max_roll('d6+14'), 20)
        self.assertEqual(dice.max_roll('2d6+14'), 26)
        self.assertEqual(dice.max_roll('2d6+14-3'), 23)
        self.assertEqual(dice.max_roll('2d6-d8+14-3'), 22)

        self.assertEqual(dice.min_roll('d6'), 1)
        self.assertEqual(dice.min_roll('d6+14'), 15)
        self.assertEqual(dice.min_roll('2d6+14'), 16)
        self.assertEqual(dice.min_roll('2d6+14-3'), 13)
        self.assertEqual(dice.min_roll('2d6-d8+14-3'), 5)

        self.assertEqual(dice.median_roll('d6'), 3.5)
        self.assertEqual(dice.median_roll('d6+14'), 17.5)
        self.assertEqual(dice.median_roll('2d6+14'), 21)
        self.assertEqual(dice.median_roll('2d6+14-3'), 18)
        self.assertEqual(dice.median_roll('2d6-d8+14-3'), 13.5)

    def testDistribution(self):
        self.assertEqual(dice.distribution('d6'), {1:1, 2:1, 3:1, 4:1, 5:1, 6:1})
        self.assertEqual(dice.distribution('d6+4'), {5:1, 6:1, 7:1, 8:1, 9:1, 10:1})
        self.assertEqual(dice.distribution('2d6'), {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

    def testChecks(self):
        self.assertEqual(dice.success_total('d6', 5), 1.0/3)
        self.assertEqual(dice.success_total('2d6', 5), 30.0/36)
        # The following methods output the result of a long sequence
        # of float arithmetic... so we'll accept within 10 decimal places.
        self.assertAlmostEqual(dice.success('d6', 6), 1.0/6, 10)
        self.assertAlmostEqual(dice.success('d6 + 15', 6+15), 1.0/6, 10)
        self.assertAlmostEqual(dice.success('2d6', 5, 1), 10.0/18, 10)

if __name__ == "__main__":
    unittest.main()
