from dice import DiceRoller
from planetsystem import PlanetSystem
from tables import StEvoTable, SequenceTable, find_solar_mass

class Star:
    roller = DiceRoller()

    def __init__(self,age):
        if age <= 0:
            raise ValueError("Age needs to be a positive number.")

        self.hasforbiddenzone = False
        self.forbiddenzone = None
        self.age = age
        self.StEvoIndex, self.mass, self.sequence, self.temperature, self.luminosity, self.radius = self.generate_star()
        self.innerlimit, self.outerlimit = self.compute_orbit_limits()
        self.snowline = self.compute_snow_line()
        self.letter = 'A'
        self.star_type = self.get_star_type()
        self.planetsystem = None

    def __repr__(self):
        return repr((self.mass, self.luminosity, self.temperature))

    def print_info(self):
        print("  Star {} Info".format(self.letter))
        print("  ---------")
        print("   Sequence:\t{}".format(self.sequence))
        print("Temperature:\t{}".format(self.temperature))
        print("       Mass:\t{}".format(self.mass))
        print(" Luminosity:\t{}".format(self.luminosity))
        print("     Radius:\t{}".format(round(self.radius, 6)))
        print("        Age:\t{}".format(round(self.age, 6)))

        # Nicely formatted orbital zone
        norzone = (round(self.innerlimit, 3), round(self.outerlimit, 3))
        print("Orbital Zne:\t{}".format(norzone))
        # Nicely formatted snow line
        nsnline = round(self.snowline, 3)
        print("  Snow Line:\t{}".format(nsnline))
        if self.hasforbiddenzone:
            # Nicely formatted forbidden zone
            nforb = [round(fz) for fz in self.forbiddenzone]
            print(" Forbid Zne:\t{}".format(nforb))
        self.planetsystem.printinfo()
        print("  ---------\n")

    def question(self, question):
        answer = input(question)

        return answer

    def generate_star(self):
        user = self.question("What is the solar mass of the star? [0.10+ or random]: ")
        mass = 0

        if user == "random":
            first_roll = self.roller.roll_dice(3,0)
            second_roll = self.roller.roll_dice(3,0)

            mass = find_solar_mass(first_roll, second_roll)

        else:
            mass = user

        seq_index = StEvoTable['mass'].index(mass)
        seq = StEvoTable['internaltype'][seq_index]
        sequence_type = StEvoTable['type'][seq_index]
        age = self.age
        sequence_index = 0

        # If we have a main-sequence-only star that can decay to a white dwarf
        if seq == 1:
            span = StEvoTable['Mspan'][seq_index]
            if age > span:
                sequence_index = 3

        # If we have a star with sub- and giant type capabilities
        elif seq == 2:
            mspan = StEvoTable['Mspan'][seq_index]
            sspan = StEvoTable['Sspan'][seq_index]
            gspan = StEvoTable['Gspan'][seq_index]
            if age > (mspan + sspan + gspan):
                sequence_index = 3
            elif age > (mspan + sspan):
                sequence_index = 2
            elif age > mspan:
                sequence_index = 1

        if sequence_index == 3:  # The star is a white dwarf, and its mass is treated specially
            mass =  self.roller.roll_dice(2, -2) * 0.05 + 0.9

        #temp
        temp = self.make_temperature(sequence_index, seq_index)
        #luminosity
        luminosity = self.make_luminosity(sequence_index, seq_index)
        #radius
        radius = self.make_radius(sequence_index, luminosity, temp)

        return seq_index, mass, sequence_type, temp, luminosity, radius

    def make_luminosity(self, SeqIndex, StEvoIndex):
        seq = SeqIndex
        age = self.age
        lmin = StEvoTable['Lmin'][StEvoIndex]
        lmax = StEvoTable['Lmax'][StEvoIndex]
        mspan = StEvoTable['Mspan'][StEvoIndex]
        lum = 0
        if seq == 0:
            # For stars with no Mspan value (mspan == 0)
            if mspan == 0:
                lum = lmin
            else:
                lum = lmin + (age / mspan * (lmax - lmin))
        elif seq == 1:  # Subgiant star
            lum = lmax
        elif seq == 2:  # Giant star
            lum = 25 * lmax
        elif seq == 3:  # White dwarf
            lum = 0.001

        return lum

    def make_temperature(self, SeqIndex,StEvoIndex):
        seq = SeqIndex
        age = self.age
        #  lmin = StEvoTable['Lmin'][self.StEvoIndex]
        #  lmax = StEvoTable['Lmax'][self.StEvoIndex]
        mspan = StEvoTable['Mspan'][StEvoIndex]
        sspan = StEvoTable['Sspan'][StEvoIndex]
        #  gspan = StEvoTable['Gspan'][self.StEvoIndex]
        if seq == 0:
            temp = StEvoTable['temp'][StEvoIndex]
        elif seq == 1:  # Subgiant star
            m = StEvoTable['temp'][StEvoIndex]
            a = age - mspan
            s = sspan
            temp = m - (a / s * (m - 4800))
        elif seq == 2:  # Giant star
            temp = self.roller.roll_dice(2, -2) * 200 + 3000
        elif seq == 3:  # White dwarf
            temp = 8000  # Not defined in the rulebook, so arbitrarily assigned

        return temp

    def make_radius(self, SeqIndex, lum, temp):
        rad = 155000 * lum ** 0.5 / temp ** 2
        if SeqIndex == 3:  # If we're a white dwarf
            rad = 0.000043  # The size is comparable to the one of Earth

        return rad

    def compute_orbit_limits(self):
        mass = self.mass
        lum = self.luminosity

        # Inner Orbital Limit
        inner1 = 0.1 * mass
        inner2 = 0.01 * lum ** 0.5
        if inner1 > inner2:
            inner_limit = inner1
        else:
            inner_limit = inner2

        # Outer Orbital Limit
        outer_limit = 40 * mass
        return inner_limit, outer_limit

    def compute_snow_line(self):
        initlum = StEvoTable['Lmin'][self.StEvoIndex]
        return 4.85 * initlum ** 0.5

    def set_forbidden_zone(self, inner, outer):
        if inner >= outer:
            raise ValueError("Inner limit must be smaller than outer limit.")
        self.forbiddenzone = (inner, outer)
        self.hasforbiddenzone = True

    def make_planetsystem(self):
        # TODO: Why not call this in the constructor and avoid this side effect too?
        self.planetsystem = PlanetSystem(self)

    def get_star_type(self) -> str:
        """
        Get the star spectral type by the star temperature
        :return: Spectral Index
        """
        sp_index = min(range(len(StEvoTable['temp'])),
                       key=lambda i: abs(StEvoTable['temp'][i] - self.temperature))
        return StEvoTable['type'][sp_index]

    def make_planetsystem(self):
        # TODO: Why not call this in the constructor and avoid this side effect too?
        self.planetsystem = PlanetSystem(self)

    def get_mass(self) -> float:
        return self.mass

    def get_age(self):
        return self.age

    def get_orbit_limits(self):
        return self.innerlimit, self.outerlimit

    def get_snowline(self):
        return self.snowline

    def get_luminosity(self):
        return self.luminosity

    def has_forbidden_zone(self):
        return self.hasforbiddenzone

    def get_forbidden_zone(self):
        return self.forbiddenzone

    def get_radius(self):
        return self.radius

    def set_letter(self, letter):
        self.letter = letter

    def get_letter(self):
        return self.letter    

    