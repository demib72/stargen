from orbitcontents import OrbitContent
from math import sqrt
from dice import DiceRoller
from tables import garden_worlds, barren_worlds, hostile_worlds, MAtmoTable, TempFactor, world_climate, SizeConstraintsTable, pressure_category, world_resource_table

class WorldPremade(OrbitContent):
    roller = DiceRoller()

    def __init__(self, parentstar, orbit):
        self.parentstar = parentstar
        self.world_size = None
        self.world_type = None
        self.generate_world_type()
        self.generate_atmosphere()
        self.hydro = self.generate_hydrographics()
        self.average_surface_temp = self.generate_average_surface_temp()
        self.world_climate = world_climate(self.average_surface_temp)
        self.blackbodytemp = self.generate_blackbody()
        self.orbit = self.create_orbit(orbit)
        OrbitContent.__init__(self, parentstar, self.orbit)
        self.density = self.make_density()
        self.diameter = self.make_diameter()
        self.gravity = self.density * self.diameter
        self.mass = self.density * self.diameter ** 3
        self.pressure, self.presscat = self.make_pressure()
        self.volcanism = ""
        self.tectonic = ""
        self.rvm = 0
        self.resources = ""
        self.habitability = 0
        self.affinity = 0

    def print_info(self):
        print("--- Planet {} Info ---".format(self.get_angled_name()))
        print("        Orbit:\t{}".format(self.orbit))
        print("   World Type:\t{} ({})".format(self.world_size, self.world_type))
        self.print_atmosphere()
        print("  Hydrogr Cov:\t{}".format(self.hydro))
        print("    Av Surf T:\t{}".format(self.average_surface_temp))
        print("      Climate:\t{}".format(self.world_climate))
        print("      Density:\t{}".format(self.density))
        print("     Diameter:\t{}".format(self.diameter))
        print("    Surf Grav:\t{}".format(self.gravity))
        print("         Mass:\t{}".format(self.mass))
        print("------------------- \n")
       
    def print_atmosphere(self):
        atcomp = self.atmcomp
        bmarg = self.hasmarginal
        marg = self.marginal
        atmcomp = [key for key in atcomp.keys() if atcomp[key] is True]
        if len(atmcomp) > 0:
            print("     Pressure:\t{} ({})".format(self.pressure, self.presscat))
            print("     Atm Comp:\t{}".format(atmcomp))
        if bmarg:
            print("     Marginal:\t{}".format(marg))

    def question(self, question):
        answer = input(question)

        return answer

    def type(self):
        return self.world_type

    def create_orbit(self, orbit):
        print(f"Orbit it {orbit} AU")
        if orbit == "":
            orbit = (77300 / self.blackbodytemp ** 2) * sqrt(self.parentstar.luminosity)
            
        return orbit

    def generate_world_type(self):
        user_answer = self.question("What is this world's type? [world type or random]: ")

        if user_answer == "random":
            first_roll = self.roller.roll_dice(3,0)
            second_roll = self.roller.roll_dice(3,0)
            
            if first_roll <= 7:
                self.world_size = hostile_worlds[second_roll][0]
                self.world_type = hostile_worlds[second_roll][1]
                print(f"The orbit is a {hostile_worlds[second_roll][0]} {hostile_worlds[second_roll][1]} planet")

            if 7 < first_roll <= 13:
                self.world_size = barren_worlds[second_roll][0]
                self.world_type = barren_worlds[second_roll][1]
                if barren_worlds[second_roll][1] == "Asteroid Belt":
                    print(f"The orbit is a {barren_worlds[second_roll][0]}")
                else:
                    print(f"The orbit is a {barren_worlds[second_roll][0]} {barren_worlds[second_roll][1]} planet")
            
            if 13 < first_roll <= 18:
                self.world_size = garden_worlds[second_roll][0]
                self.world_type = garden_worlds[second_roll][1]
                print(f"The orbit is a {garden_worlds[second_roll][0]} {garden_worlds[second_roll][1]} planet")

        if user_answer != "random":
            self.world_size = self.question("What is the size of the world? [Tiny, Small, Standard, or Large]: ")
            self.world_type = user_answer

    def get_size(self):
        return self.world_size

    def get_type(self):
        return self.world_type

    def generate_atmosphere(self):
        # Determine atmospheric mass
        if self.world_size == 'Tiny' or self.world_type == 'Hadean' or self.world_type == 'Chthonian' or self.world_type == 'Rock':
            self.atmmass = 0
        else:
            self.atmmass = self.roller.roll_dice(3, 0) / 10.

        # Now determine atmospheric composition
        if self.atmmass != None:
            self.atmcomp = {
                'Corrosive': False,
                'Mildly Toxic': False,
                'Highly Toxic': False,
                'Lethally Toxic': False,
                'Suffocating': False
            }
            self.hasmarginal = False
            self.marginal = ''
        if self.world_size == 'Small' and type == 'Ice':
            self.atmcomp['Suffocating'] = True
            if self.roller.roll_dice(3, 0) > 15:
                self.atmcomp['Lethally Toxic'] = True
            else:
                self.atmcomp['Mildly Toxic'] = True

        if self.world_type == 'Ammonia' or self.world_type == 'Greenhouse':
            self.atmcomp['Suffocating'] = True
            self.atmcomp['Lethally Toxic'] = True
            self.atmcomp['Corrosive'] = True

        if self.world_type == 'Garden':
            if self.roller.roll_dice(3, 0) >= 12:
                self.hasmarginal = True
                self.marginal = MAtmoTable[self.roller.roll_dice(3, 0)]

        if self.world_size == 'Standard' and (self.world_type == 'Ice' or self.world_type == 'Ocean'):
            self.atmcomp['Suffocating'] = True
            if self.roller.roll_dice(3, 0) > 12:
                self.atmcomp['Mildly Toxic'] = True

        if self.world_size == 'Large' and (self.world_type == 'Ice' or self.world_type == 'Ocean'):
            self.atmcomp['Highly Toxic'] = True
            self.atmcomp['Suffocating'] = True

    def get_marginal(self):
        """
        Returns a tuple of bool and atmosphere.
        """
        return self.hasmarginal, self.marginal


    def generate_hydrographics(self):
        percentage = self.question("How much water is on the planet? [percentage or random]: ")

        if percentage == "random":
            hydro = 0
            size = self.world_size
            type = self.world_type
            if size == 'Small' and type == 'Ice':
                hydro = self.roller.roll_dice(1, 2) * 10
            if type == 'Ammonia':
                hydro = self.roller.roll_dice(2, 0) * 10
                if hydro > 100:
                    hydro = 100
            if type == 'Ice' and (size == 'Standard' or size == 'Large'):
                hydro = self.roller.roll_dice(2, -10) * 10
            if type == 'Ocean' or type == 'Garden':
                bonus = 4
                if size == 'Large':
                    bonus = 6
                hydro = self.roller.roll_dice(1, bonus) * 10
                if hydro > 100:
                    hydro = 100
            if type == 'Greenhouse':
                hydro = self.roller.roll_dice(2, -7) * 10
            # Introduce a small amount of randomness to the hydrographic coverage,
            # to make the worlds more varied and to make them feel more real
            # Do this only if there is any surface liquid at all,
            # avoiding those astral bodies who cannot have a hydrographic coverage at all
            # Vary by +- 5% as described in the rule book
            if 10 <= hydro <= 90:
                sign = self.roller.roll_dice(1, 0, 2)
                variation = self.roller.roll_dice(1, 0, 5)
                if sign == 1:
                    hydro += variation
                else:
                    hydro -= variation

            return hydro
        else:
            return float(percentage)

    def get_hydrographic_cover(self):
        return self.hydro

    def get_absorption_greenhouse(self):
        """
        Return a tuple (absorption factor, greenhouse factor) based on world
        type and size.
        """
        world_type = self.world_type
        size = self.world_size
        if world_type != 'Garden' and world_type != 'Ocean':
            return TempFactor[world_type][size]
        else:
            hydro = self.hydro
            absorption = 0.84
            if hydro <= 90:
                absorption = 0.88
            if hydro <= 50:
                absorption = 0.92
            if hydro <= 20:
                absorption = 0.95
            
            return absorption, 0.16

    def generate_average_surface_temp(self):
        size = self.world_size
        type_ = self.world_type
        climate_question = self.question("What is the average surface temperature of the world? [140+ or random]: ")

        if climate_question == "random":
            roll_result = self.roller.roll_dice(3,-3)

            if type_ == "Asteroid Belt":
                average_surface_temp = (roll_result * 24) + 140
            
            elif size == "Tiny" and type_ == "Sulfur" or type_ == "Ice":
                average_surface_temp = (roll_result * 4) + 80

            elif size == "Tiny" and type_ == "Rock":
                average_surface_temp = (roll_result * 24) + 140

            elif size == "Small" and type_ == "Hadean":
                average_surface_temp = (roll_result * 2) + 50

            elif size == "Small" and type_ == "Ice":
                average_surface_temp = (roll_result * 4) + 80

            elif size == "Small" and type_ == "Rock":
                average_surface_temp = (roll_result * 24) + 140

            elif size == "Standard" and type_ == "Hadean":
                average_surface_temp = (roll_result * 2) + 50

            elif size == "Standard" and type_ == "Ammonia":
                average_surface_temp = (roll_result * 5) + 140

            elif size == "Standard" and type_ == "Ice":
                average_surface_temp = (roll_result * 10) + 80

            elif size == "Standard" and type_ == "Garden" or type_ == "Ocean":
                average_surface_temp = (roll_result * 6) + 250

            elif size == "Standard" and type_ == "Greenhouse" or type_ == "Chthonian":
                average_surface_temp = (roll_result * 30) + 500 

            elif size == "Large" and type_ == "Ammonia":
                average_surface_temp = (roll_result * 5) + 140

            elif size == "Large" and type_ == "Ice":
                average_surface_temp = (roll_result * 10) + 80
                
            elif size == "Large" and type_ == "Garden" or type_ == "Ocean":
                average_surface_temp = (roll_result * 6) + 250
                
            elif size == "Large" and type_ == "Greenhouse" or type_ == "Chthonian":
                average_surface_temp = (roll_result * 30) + 500
            else:
                print("error")
        else:
            average_surface_temp = int(climate_question)
        
        return average_surface_temp

    def get_climate(self):
        return self.world_climate

    def get_average_surface_temp(self):
        return self.average_surface_temp

    def generate_blackbody(self):
        abs, green = self.get_absorption_greenhouse()
        matm = self.atmmass
        bbcorr = abs * (1 + (matm * green))
        
        return self.average_surface_temp / bbcorr

    def make_density(self) -> float:
        type = self.world_type
        size = self.world_size
        
        dice = self.roller.roll_dice(3, 0)

        if type == 'Ammonia' or type == 'Hadean' or type == 'Sulfur' or (type == 'Ice' and size != 'Large'):
            if dice >= 3:
                density = 0.3
            if dice >= 7:
                density = 0.4
            if dice >= 11:
                density = 0.5
            if dice >= 15:
                density = 0.6
            if dice == 18:
                density = 0.7
        elif type == 'Asteroid Belt':
            density = 0.0
        elif type == 'Rock':
            if dice >= 3:
               density = 0.6
            if dice >= 7:
                density = 0.7
            if dice >= 11:
                density = 0.8
            if dice >= 15:
                density = 0.9
            if dice == 18:
                density = 1.0
        else:
            if dice >= 3:
                density = 0.8
            if dice >= 7:
                density = 0.9
            if dice >= 11:
                density = 1.0
            if dice >= 15:
                density = 1.1
            if dice == 18:
                density = 1.2

        return density

    def make_diameter(self) -> float:
        size = self.world_size
        bb = self.blackbodytemp
        dens = self.density

        print(dens)

        if dens == 0.0:
            diam = 0.0
        else:
            smin, smax = SizeConstraintsTable[size]
            term = (bb / dens) ** (0.5)
            min = term * smin
            max = term * smax
            diff = max - min
            diam = self.roller.roll_dice(2, -2) * 0.1 * diff + min
        
        return diam

    def make_pressure(self) -> tuple:
        size = self.world_size
        type = self.world_type
        pressure = 0
        if size == 'Tiny' or type == 'Hadean':
            category = 'None'
        elif type == 'Chthonian':
            category = 'Trace'
        elif size == 'Small' and type == 'Rock':
            category = 'Trace'
        else:
            factor = 1
            if size == 'Small' and type == 'Ice':
                factor = 10
            if size == 'Large':
                factor = 5
            if type == 'Greenhouse':
                factor *= 100
            pressure = self.mass * factor * self.gravity
            category = pressure_category(pressure)
        return pressure, category

    def get_density(self):
        return self.density

    def get_diameter(self):
        return self.diameter

    def make_gravity(self) -> float or int:
        return self.density * self.diameter

    def get_gravity(self) -> float or int:
        return self.gravity

    def make_mass(self) -> float or int:
        return self.density * self.diameter ** 3

    def get_mass(self) -> float or int:
        return self.mass

    def make_pressure(self) -> tuple:
        size = self.world_size
        type = self.world_type
        pressure = 0
        if size == 'Tiny' or type == 'Hadean':
            category = 'None'
        elif type == 'Chthonian':
            category = 'Trace'
        elif size == 'Small' and type == 'Rock':
            category = 'Trace'
        else:
            factor = 1
            if size == 'Small' and type == 'Ice':
                factor = 10
            if size == 'Large':
                factor = 5
            if type == 'Greenhouse':
                factor *= 100
            pressure = self.get_mass() * factor * self.get_gravity()
            category = pressure_category(pressure)
        return pressure, category

    def get_pressure(self):
        return self.pressure

    def get_pressure_category(self):
        return self.presscat

    def make_volcanism(self):
        bonus = round(self.get_gravity() / self.primary_star.get_age() * 40)
        bonus += self.get_volcanic_bonus()
        volcanoroll = self.roller.roll_dice(3, bonus)
        activity = 'None'
        if volcanoroll > 16:
            activity = 'Light'
        if volcanoroll > 20:
            activity = 'Moderate'
        if volcanoroll > 26:
            activity = 'Heavy'
        if volcanoroll > 70:
            activity = 'Extreme'
        return activity

    def get_volcanism(self):
        return self.volcanism

    def get_volcanic_bonus(self):
        return 0

    def make_tectonism(self):
        if self.world_size == 'Small' or self.world_size == 'Tiny':
            return 'None'
        else:
            volc = self.get_volcanism()
            bonus = 0
            if volc == 'None':
                bonus -= 8
            if volc == 'Light':
                bonus -= 4
            if volc == 'Heavy':
                bonus += 4
            if volc == 'Extreme':
                bonus += 8
            if self.get_hydrographic_cover() < 50:
                bonus -= 2
            bonus += self.get_tectonic_bonus()
            tect = self.roller.roll_dice(3, bonus)
            activity = 'None'
            if tect > 6:
                activity = 'Light'
            if tect > 10:
                activity = 'Moderate'
            if tect > 14:
                activity = 'Heavy'
            if tect > 18:
                activity = 'Extreme'
            return activity

    def get_tectonic_bonus(self):
        return 0

    def get_tectonics(self):
        return self.tectonic

    def get_resourcebonus(self):
        volc = self.get_volcanism()
        bonus = 0
        if volc == 'None':
            bonus -= 2
        if volc == 'Light':
            bonus -= 1
        if volc == 'Heavy':
            bonus += 1
        if volc == 'Extreme':
            bonus += 2
        return bonus

    def make_resources(self):
        """
        Return resource value modifier (RVM) and corresponding string
        """
        rollbonus = self.get_resourcebonus()
        dice = self.roller.roll_dice(3, rollbonus)
        return world_resource_table[dice]

    def get_rvm(self):
        return self.rvm

    def get_resources(self):
        return self.resources

    def make_habitability(self):
        modifier = 0
        # The following is from p. 121
        volc = self.get_volcanism()
        tect = self.get_tectonics()
        if volc == 'Heavy':
            modifier -= 1
        if volc == 'Extreme':
            modifier -= 2
        if tect == 'Heavy':
            modifier -= 1
        if tect == 'Extreme':
            modifier -= 2

        # Now comes standard implementation, p. 88
        # First: Based on breathable or non-breathable atmosphere
        atmo = [key for key in self.atmcomp.keys() if self.atmcomp[key] is True]
        if len(atmo) > 0:
            # Non-breathable atmosphere
            if len(atmo) == 2:
                # Suffocating and Toxic
                modifier -= 1
            elif len(atmo) == 3:
                # Suffocating, Toxic and Corrosive
                modifier -= 2
        else:
            # Breathable atmosphere
            press = self.get_pressure_category()
            if press == 'Very Thin':
                modifier += 1
            if press == 'Thin':
                modifier += 2
            if press == 'Standard' or press == 'Dense':
                modifier += 3
            if press == 'Very Dense' or press == 'Superdense':
                modifier += 1
            hasmarg, marg = self.get_marginal()
            if not hasmarg:
                modifier += 1
            climate = self.get_climate()
            if climate == 'Cold' or climate == 'Hot':
                modifier += 1
            if climate in ['Chilly', 'Cool', 'Normal', 'Warm', 'Tropical']:
                modifier += 2

        # Now the Hydrographics Coverage conditions
        if self.get_type() in ['Garden', 'Ocean']:
            hydro = self.get_hydrographic_cover()
            if (0 < hydro < 60) or (90 < hydro < 100):
                modifier += 1
            elif hydro > 0:
                modifier += 2

        # Check lower bounds (p. 121)
        if modifier < -2:
            modifier = -2
        return modifier

    def get_habitability(self):
        return self.habitability

    def make_affinity(self):
        return self.get_rvm() + self.get_habitability()

    def get_affinity(self):
        return self.affinity