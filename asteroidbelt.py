from orbitcontents import OrbitContent
from tables import world_climate, asteroid_resource_table


class AsteroidBelt(OrbitContent):
    """
    Class for asteroid belts.
    """
    def __init__(self, primarystar, orbitalradius):
        OrbitContent.__init__(self, primarystar, orbitalradius)
        self.rvm, self.resources = self.make_resources()
        self.avsurf = self.make_surface_temp()
        self.climate = self.make_climate()
        self.habitability = 0
        self.affinity = self.habitability + self.rvm

    def __repr__(self):
        return repr("Asteroid Belt")

    def type(self):
        return "Ast. Belt"

    def print_info(self):
        print("Asteroid Belt {}".format(self.get_angled_name()))
        print("    Orbit:\t{}".format(self.get_orbit()))
        print("  Orb Per:\t{}".format(self.get_period()))
        print("  Orb Ecc:\t{}".format(self.get_eccentricity()))
        print("      RVM:\t{}".format(self.rvm))
        print("   Res. V:\t{}".format(self.resources))
        print("     Aff.:\t{}".format(self.affinity))
        print("")

    def make_resources(self):
        """
        Return resource value modifier (RVM) and corresponding string
        """
        dice = self.roller.roll_dice(3, 0)
        return asteroid_resource_table[dice]

    def make_surface_temp(self):
        return self.get_blackbody_temp() * 0.97

    def get_average_surface_temp(self):
        return self.avsurf

    def make_climate(self):
        return world_climate(self.get_average_surface_temp())

    def get_climate(self):
        return self.climate

    def get_resources(self):
        return self.resources

    def get_rvm(self):
        return self.rvm

    def get_affinity(self):
        return self.affinity