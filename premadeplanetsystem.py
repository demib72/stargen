from dice import DiceRoller
from gasgiant import GasGiant
from asteroidbelt import AsteroidBelt
from planet import Planet
from tables import OrbitalSpace
from planetpremade import PlanetPremade

class PreMadePlanetSystem:
    roller = DiceRoller()
    def __init__(self, parentstar) -> None:
        self.parentstar = parentstar
        self.innerlimit, self.outerlimit = parentstar.get_orbit_limits()
        self.snowline = parentstar.get_snowline()
        self.primarylum = parentstar.get_luminosity()
        self.forbidden = parentstar.has_forbidden_zone()
        if self.forbidden:
            self.innerforbidden, self.outerforbidden = parentstar.get_forbidden_zone()
        self.premade_world, self.premade_orbit = self.premade()
        self.make_gasgiant_arrangement()
        self.place_first_gasgiant()
        self.createorbits()
        self.make_content_list()
        self.place_gas_giants()
        self.fill_orbits()
        self.name_contents()
        self.make_eccentricities()

    def printinfo(self):
        print("--------------------")
        print(" Planet System Info ")
        print("--------------------")
        print("GG Arrngmnt:\t{}".format(self.gasarrangement))
        # Nicely formatted first gas giant orbit
        nggorb = round(self.firstgasorbit, 3)
        print("Frst GG Orb:\t{}".format(nggorb))
        # Nicely formatted orbits
        norb = [round(orb, 3) for orb in self.orbitarray]
        print("     Orbits:\t{}".format(norb))
        # Beautifully formatted listing of orbits and contents
        self.printorbcontent()
        self.listorbcontentdetails()
    
    def printorbcontent(self):
        first = True
        for skey in sorted(self.orbitcontents):
            if first:
                print("Orb Content:\t{}: {}".format(round(skey, 3), self.orbitcontents[skey]))
                first = False
            else:
                print("\t\t{}: {}".format(round(skey, 3), self.orbitcontents[skey]))

    def question(self, question):
        answer = input(question)

        return answer

    def listorbcontentdetails(self):
        for skey in sorted(self.orbitcontents):
            self.orbitcontents[skey].print_info()

    def get_orbitcontents(self):
        return self.orbitcontents

    def allowed_orbit(self, testorbit):
        result = testorbit >= self.innerlimit
        result &= testorbit <= self.outerlimit
        if self.forbidden and result:
            result2 = testorbit <= self.innerforbidden
            result2 |= testorbit >= self.outerforbidden
            return result & result2
        else:
            return result

    def premade(self):
        answer = input("Would you like to make a premade world? [Y/N]: ")
        premade = ""
        orbit = ""

        if answer == "Y":
            premade =  PlanetPremade(self.parentstar)
            orbit = premade.orbit
        else:
            premade = None
            orbit = None

        return premade, orbit
        
    def make_gasgiant_arrangement(self):
        user = self.question("Do you want to randomly determine Gas Giant Arrangement? [Y/N]: ")

        if user == "Y":
            dice = self.roller.roll_dice(3, 0)
            self.gasarrangement = 'None'
            if dice > 10:
                self.gasarrangement = 'Conventional'
            if dice > 12:
                self.gasarrangement = 'Eccentric'
            if dice > 14:
                self.gasarrangement = 'Epistellar'
            if self.forbidden:
                if self.snowline > self.innerforbidden and self.snowline < self.outerforbidden:
                    self.gasarrangement = 'None'
        else:
            if self.forbidden:
                if self.snowline > self.innerforbidden and self.snowline < self.outerforbidden:
                    self.gasarrangement = 'None'
            else:
                self.gasarrangement = self.question("What is the arrangement? [None, Conventional, Eccentric, or Epistellar]: ")

    def place_first_gasgiant(self):
        orbit = 0
        if self.gasarrangement == 'Conventional':
            orbit = (1 + (self.roller.roll_dice(2, -2) * 0.05)) * self.snowline
        if self.gasarrangement == 'Eccentric':
            orbit = self.roller.roll_dice(1, 0) * 0.125 * self.snowline
        if self.gasarrangement == 'Epistellar':
            orbit = self.roller.roll_dice(3, 0) * 0.1 * self.innerlimit
        self.firstgasorbit = orbit

    def createorbits(self):
        orbits = []
        if self.gasarrangement == 'None':
            # Create orbits outwards from the innermost limit
            if self.forbidden and self.innerforbidden < self.innerlimit:
                innermost = self.outerforbidden
            else:
                innermost = self.innerlimit
            orbits += [innermost]
            orbitsout = self.orbit_outward(innermost)
            orbits += orbitsout
        elif self.gasarrangement == 'Epistellar':
            # Create orbits outwards. Since the epistellar GasGiant is closer to
            # the star than the inner orbital limit, special conditions apply
            if self.premade_world == None:
                orbits += [self.firstgasorbit]
            else:
                orbits += [self.firstgasorbit, self.premade_orbit]
            startorbit = self.firstgasorbit + 0.15
            # If the minimal distance is not within the orbital zone make the
            # next orbit right at the border
            if not self.allowed_orbit(startorbit):
                startorbit = self.innerlimit
            orbits += [startorbit]
            orbitsout = self.orbit_outward(startorbit)
            orbits += orbitsout
        else:
            # Create orbits inwards then outwards from first gas giant
            if self.premade_world == None:
                orbits += [self.firstgasorbit]
            else:
                orbits += [self.firstgasorbit, self.premade_orbit]
            orbitsin = self.orbit_inward(self.firstgasorbit, self.premade_orbit)
            orbitsout = self.orbit_outward(self.firstgasorbit)
            orbits = orbitsin + orbits
            orbits += orbitsout
        self.orbitarray = orbits

    def orbit_outward(self, startorbit):
        allowed = True
        orbits = []
        old_orbit = startorbit
        new_orbit = 0
        while (allowed):
            orbital_separation = OrbitalSpace[self.roller.roll_dice(3, 0)]
            new_orbit = old_orbit * orbital_separation
            if self.allowed_orbit(new_orbit) and new_orbit - old_orbit >= 0.15:
                orbits += [new_orbit]
                old_orbit = new_orbit
            else:
                allowed = False
                new_orbits = [old_orbit * 1.4, old_orbit * 2.0]
                success = False
                # Check 1.4 and 2.0 if allowed, take the first
                for possible_orbit in new_orbits:
                    if self.allowed_orbit(possible_orbit):
                        if possible_orbit - old_orbit >= 0.15:
                            success = True
                            new_orbit = possible_orbit
                            old_orbit = possible_orbit
                            break
                if success:
                    orbits += [new_orbit]
                    allowed = True
                else:
                    # If our searching yielded nothing, check if there is an
                    # allowed orbit with the minimal distance, and put that
                    if self.allowed_orbit(old_orbit + 0.15) and self.allowed_orbit(old_orbit * 1.4):
                        new_orbit = old_orbit + 0.15
                        orbits += [new_orbit]
                        old_orbit = new_orbit
                        allowed = True

        return orbits

    def orbit_inward(self, startorbit, premadeorbit):
        allowed = True
        orbits = []
        oldorbit = startorbit
        neworbit = 0
        while (allowed):
            orbsep = OrbitalSpace[self.roller.roll_dice(3, 0)]
            neworbit = oldorbit / orbsep
            if self.allowed_orbit(neworbit) and oldorbit - neworbit >= 0.15:
                print(self.premade_world)
                if self.premade_world != None:
                    if 1.4 < neworbit / premadeorbit <= 1.6:
                        neworbit = premadeorbit
                else:
                    orbits = [neworbit] + orbits
                    oldorbit = neworbit
            else:
                allowed = False
                # Check to fit one last orbit
                neworbit = oldorbit / 1.4
                if self.allowed_orbit(neworbit) and oldorbit - neworbit >= 0.15:
                    orbits = [oldorbit / 1.4] + orbits
                    # Because this worked we'll try to do this one more time
                    oldorbit = oldorbit / 1.4
                    allowed = True
        return orbits

    def make_content_list(self):
        """
        Initialize orbit content dictionary

        Make a dictionary: Orbit: Content. Initially this will only contain the
        first gas giant. (If gas giant arrangement is not "None")
        """
        self.orbitcontents = dict.fromkeys(self.orbitarray)

        if self.premade_world != "":
            self.orbitcontents[self.premade_orbit] = self.premade_world

        # Put the first gas giant
        if self.gasarrangement != 'None':
            # Check whether roll bonus for size is applicable here
            bonus = self.gas_giant_bonus(self.firstgasorbit)

            # Add a GasGiant to the dict
            self.orbitcontents[self.firstgasorbit] = GasGiant(
                self.parentstar, self.firstgasorbit, bonus)

    def place_gas_giants(self):
        """
        Populate orbit content dictionary with gas giants

        Iterate through all empty orbits and decide whether to place a gas
        giant there. Also check whether the orbit is eligible for a bonus.
        """

        rollorbits = [orb for orb in self.orbitarray if self.orbitcontents[orb] == None]
        small_orbits = [orb for orb in rollorbits if orb < self.snowline]
        large_orbits = [orb for orb in rollorbits if orb > self.snowline]
        if self.gasarrangement == 'Epistellar':
            for stellar_orbit in small_orbits:
                if self.roller.roll_dice(3, 0) <= 6:
                    self.orbitcontents[stellar_orbit] = GasGiant(self.parentstar,
                                                                   stellar_orbit, True)
            for stellar_orbit in large_orbits:
                if self.roller.roll_dice(3, 0) <= 14:
                    self.orbitcontents[stellar_orbit] = GasGiant(self.parentstar,
                                                                   stellar_orbit, self.gas_giant_bonus(stellar_orbit))
        elif self.gasarrangement == 'Eccentric':
            for stellar_orbit in small_orbits:
                if self.roller.roll_dice(3, 0) <= 8:
                    self.orbitcontents[stellar_orbit] = GasGiant(self.parentstar,
                                                                   stellar_orbit, True)
            for stellar_orbit in large_orbits:
                if self.roller.roll_dice(3, 0) <= 14:
                    self.orbitcontents[stellar_orbit] = GasGiant(self.parentstar,
                                                                   stellar_orbit, self.gas_giant_bonus(stellar_orbit))
        elif self.gasarrangement == 'Conventional':
            for stellar_orbit in large_orbits:
                if self.roller.roll_dice(3, 0) <= 15:
                    self.orbitcontents[stellar_orbit] = GasGiant(self.parentstar,
                                                                   stellar_orbit, self.gas_giant_bonus(stellar_orbit))

    def gas_giant_bonus(self, orbit):
        bonus = orbit <= self.snowline
        if not bonus:
            gg_index = self.orbitarray.index(orbit)
            if gg_index > 0:
                bonus = self.orbitarray[gg_index - 1] < self.snowline
        return bonus

    def fill_orbits(self):
        """
        Fill empty orbits with non-jovian entities (worlds and asteroid belts)
        """

        # Determine eligible orbits to roll for
        roll_orbits = [orb for orb in self.orbitarray if self.orbitcontents[orb] == None]
        roll_orbits.sort()
        # Go through these orbits and determine the contents
        for orbit in roll_orbits:
            user = self.question("Do you want to randomly determine world?[Y/N]: ")

            if user == "Y":
                roll_mod = self.orbit_fill_modifier(self.orbitarray.index(orbit))
                dice_roll = self.roller.roll_dice(3, roll_mod)
                if 4 <= dice_roll <= 6:
                    obj = AsteroidBelt(self.parentstar, orbit)
                if 7 <= dice_roll <= 8:
                    obj = Planet(self.parentstar, orbit, "Tiny")
                if 9 <= dice_roll <= 11:
                    obj = Planet(self.parentstar, orbit, "Small")
                if 12 <= dice_roll <= 15:
                    obj = Planet(self.parentstar, orbit, "Standard")
                if dice_roll >= 16:
                    obj = Planet(self.parentstar, orbit, "Large")
                if not dice_roll <= 3:
                    self.orbitcontents[orbit] = obj
            else:
                obj = PlanetPremade(self.parentstar, orbit)
        # Now remove all orbits that still have None as content
        orc = {k: v for k, v in self.orbitcontents.items() if v != None}
        self.orbitcontents = orc

    def name_contents(self):
        counter = 0

        for key in sorted(self.orbitcontents):
            counter += 1
            name = '{}-{}'.format(self.parentstar.get_letter(), counter)
            self.orbitcontents[key].set_name(name)
            self.orbitcontents[key].set_number(counter)

    def orbit_fill_modifier(self, orbitindex):
        modifier = 0
        orbits = self.orbitarray
        # If the orbit is adjacent to a forbidden zone
        if self.forbidden:
            if orbitindex == 0 and self.outerforbidden < orbits[orbitindex]:
                modifier -= 6
            if orbitindex == len(orbits) - 1 and self.innerforbidden > orbits[orbitindex]:
                modifier -= 6

        # If the orbit is adjacent to the inner or outer limit
        if orbitindex == 0 or orbitindex == len(orbits) - 1:
            modifier -= 3

        # If the next orbit outward is occupied by a gas giant
        if orbitindex != len(orbits) - 1:
            if self.orbitcontents[orbits[orbitindex + 1]] != None:
                if self.orbitcontents[orbits[orbitindex + 1]].type() == "Gas Giant":
                    modifier -= 6

        # If the next orbit inward is occupied by a gas giant
        if orbitindex != 0:
            if self.orbitcontents[orbits[orbitindex - 1]] != None:
                if self.orbitcontents[orbits[orbitindex - 1]].type() == "Gas Giant":
                    modifier -= 3

        return modifier

    def make_eccentricities(self):
        for k, oc in self.orbitcontents.items():
            if self.gasarrangement == 'Conventional':
                bonus = -6
            elif k == list(self.orbitcontents)[0] \
                    and self.gasarrangement == 'Epistellar' and oc.type() == 'Gas Giant':
                bonus = -6
            elif self.gasarrangement == 'Eccentric' and oc.type() == 'Gas Giant' and k < self.snowline:
                bonus = +4
            else:
                bonus = 0
            oc.eccentricity = oc.make_eccentricity(self.roller.roll_dice(3, bonus))
            oc.min_max = oc.make_min_max()