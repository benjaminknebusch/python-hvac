"""
Cooling load calculation of exposition hall 9 and 10.

The exposition hall has three exterior walls (north, west, and east). The
roof has two skylights. The exterior walls have no windows. Heat flows
through interior partition walls are assumed zero. The building can be
considered as one single space. The building's floor area is 18,68 m x 28,02 m
= 523,4136 m². The building height is 6 m.

More information about the cooling load calculation API can be found in the
file "info.md" in docs/examples/heating_load_calc.
"""
from datetime import date
import pandas as pd
from hvac import Quantity
from hvac.charts import LineChart
from hvac.cooling_load_calc import (
    Geometry,
    HeatFlowDirection,
    Material,
    SurfaceLayer,
    BuildingComponent,
    AirSpace,
    ConstructionAssembly,
    WindowThermalProperties,
    Space,
    VentilationZone,
    BuildingEntity,
    Building,
    Location,
    ClimateData,
    TemperatureSchedule,
    OnOffSchedule,
    OccupancySchedule,
    InternalHeatGain,
    PeopleHeatGain
)

Q_ = Quantity


class ConstructionAssemblies:
    """
    Class that groups the construction assemblies from which the elements of
    the building envelope are to be made.
    """
    @staticmethod
    def exterior_wall_light(
        T_ext: Quantity,
        T_int: Quantity,
        T_asp: Quantity,
        dT_asp: Quantity,
        v_wind: Quantity,
        t_ins: Quantity
    ) -> ConstructionAssembly:
        """
        Creates the construction assembly of a light-weight exterior wall.

        Parameters
        ----------
        T_ext:
            outdoor air temperature
        T_int:
            indoor air temperature
        T_asp:
            mean airspace temperature
        dT_asp:
            temperature difference across airspace
        v_wind:
            wind speed
        t_ins:
            thickness of the insulation layer

        Returns
        -------
        ConstructionAssembly
        """
        # Create the layers that compose the construction assembly:
        ext_surf_film = SurfaceLayer.create(
            ID='ext_surf_film',
            geometry=Geometry(),
            heat_flow_direction=HeatFlowDirection.HORIZONTAL,
            Tmn=T_ext,
            internal_surface=False,
            wind_speed=v_wind
        )

        cement_plaster = BuildingComponent.create(
            ID='cement_plaster',
            geometry=Geometry(t=Q_(10, 'mm')),
            material=Material(
                k=Q_(0.950, 'W / (m * K)'),
                rho=Q_(1900, 'kg / m ** 3'),
                c=Q_(840, 'J / (kg * K)')
            )
        )

        chipboard = BuildingComponent.create(
            ID='chipboard',
            geometry=Geometry(t=Q_(25, 'mm')),
            material=Material(
                k=Q_(0.100, 'W / (m * K)'),
                rho=Q_(450, 'kg / m ** 3'),
                c=Q_(1880, 'J / (kg * K)')
            )
        )

        air_gap = AirSpace.create(
            ID='air_gap',
            geometry=Geometry(t=Q_(40, 'mm')),
            dT=dT_asp,
            heat_flow_direction=HeatFlowDirection.HORIZONTAL,
            Tmn=T_asp
        )

        insulation = BuildingComponent.create(
            ID='insulation',
            geometry=Geometry(t=t_ins),
            material=Material(
                k=Q_(0.035, 'W / (m * K)'),
                rho=Q_(35, 'kg / m ** 3'),
                c=Q_(840, 'J / (kg * K)')
            )
        )
        insulation.slices = 7
        # The insulation layer is divided in a number of slices from which the
        # linear thermal network model of the exterior wall will be derived.
        # (Each slice will represent a temperature node in the linear thermal
        # network model of the wall. By default, a layer has always only one
        # temperature node in which all the heat capacity of the layer is
        # thought to be concentrated.)

        plasterboard = BuildingComponent.create(
            ID='plasterboard',
            geometry=Geometry(t=Q_(13, 'mm')),
            material=Material(
                k=Q_(0.230, 'W / (m * K)'),
                rho=Q_(900, 'kg / m ** 3'),
                c=Q_(840, 'J / (kg * K)')
            )
        )

        int_surf_film = SurfaceLayer.create(
            ID='int_surf_film',
            geometry=Geometry(),
            heat_flow_direction=HeatFlowDirection.HORIZONTAL,
            Tmn=T_int
        )

        # Create the construction assembly of the exterior wall:
        ext_wall = ConstructionAssembly.create(
            ID=f"ext_wall_type1 (t_ins = {t_ins.to('mm'):~P.0f})",
            # Layers must be ordered from the outdoor to the indoor:
            layers=[
                ext_surf_film,
                cement_plaster,
                chipboard,
                air_gap,
                insulation,
                plasterboard,
                int_surf_film
            ]
        )
        return ext_wall

    @staticmethod
    def exterior_wall_heavy(
        T_ext: Quantity,
        T_int: Quantity,
        v_wind: Quantity,
        t_ins: Quantity
    ) -> ConstructionAssembly:
        """
        Creates the construction assembly of a heavy-weight exterior wall.

        Parameters
        ----------
        See `create_exterior_wall_light`.

        Returns
        -------
        ConstructionAssembly
        """
        ext_surf_film = SurfaceLayer.create(
            ID='ext_surf_film',
            geometry=Geometry(),
            heat_flow_direction=HeatFlowDirection.HORIZONTAL,
            Tmn=T_ext,
            internal_surface=False,
            wind_speed=v_wind
        )

        concrete_wall = BuildingComponent.create(
            ID='concrete_wall',
            geometry=Geometry(t=Q_(14, 'cm')),
            material=Material(
                k=Q_(1.19, 'W / (m * K)'),
                rho=Q_(1700, 'kg / m ** 3'),
                c=Q_(1000, 'J / (kg * K)')
            )
        )
        concrete_wall.slices = 7

        insulation = BuildingComponent.create(
            ID='insulation',
            geometry=Geometry(t=t_ins),
            material=Material(
                k=Q_(0.04, 'W / (m * K)'),
                rho=Q_(22.0, 'kg / m ** 3'),
                c=Q_(1030, 'J / (kg * K)')
            )
        )
        insulation.slices = 7

        int_surf_film = SurfaceLayer.create(
            ID='int_surf_film',
            geometry=Geometry(),
            heat_flow_direction=HeatFlowDirection.HORIZONTAL,
            Tmn=T_int
        )

        ext_wall = ConstructionAssembly.create(
            ID=f"ext_wall_type1 (t_ins = {t_ins.to('mm'):~P.0f})",
            layers=[
                ext_surf_film,
                concrete_wall,
                insulation,
                int_surf_film
            ]
        )
        return ext_wall

    @staticmethod
    def roof(
        T_ext: Quantity,
        T_int: Quantity,
        v_wind: Quantity,
        t_ins: Quantity,
        heat_flow_dir: HeatFlowDirection
    ) -> ConstructionAssembly:
        """
        Creates the construction assembly of the roof.

        Parameters
        ----------
        `heat_flow_dir`:
            Indication of the direction of heat flow through the construction
            assembly.

        Other Parameters
        ----------------
        See `create_exterior_wall_light`.
        """
        ext_surf_film = SurfaceLayer.create(
            ID='ext_surf_film',
            geometry=Geometry(),
            heat_flow_direction=heat_flow_dir,
            Tmn=T_ext,
            internal_surface=False,
            wind_speed=v_wind
        )

        roofing_felt = BuildingComponent.create(
            ID='roofing_felt',
            geometry=Geometry(t=Q_(3, 'mm')),
            material=Material(
                k=Q_(0.170, 'W / (m * K)'),
                rho=Q_(1200, 'kg / m ** 3'),
                c=Q_(1470, 'J / (kg * K)')
            )
        )
        roofing_felt.slices = 3

        insulation = BuildingComponent.create(
            ID='insulation',
            geometry=Geometry(t=t_ins),
            material=Material(
                k=Q_(0.035, 'W / (m * K)'),
                rho=Q_(15, 'kg / m ** 3'),
                c=Q_(1470, 'J / (kg * K)')
            )
        )
        insulation.slices = 8

        concrete = BuildingComponent.create(
            ID='concrete',
            geometry=Geometry(t=Q_(100, 'mm')),
            material=Material(
                k=Q_(1.9, 'W / (m * K)'),
                rho=Q_(2500, 'kg / m ** 3'),
                c=Q_(840, 'J / (kg * K)')
            )
        )
        concrete.slices = 10

        int_surf_film = SurfaceLayer.create(
            ID='int_surf_film',
            geometry=Geometry(),
            heat_flow_direction=heat_flow_dir,
            Tmn=T_int
        )

        roof = ConstructionAssembly.create(
            ID='roof',
            layers=[
                ext_surf_film,
                roofing_felt,
                insulation,
                concrete,
                int_surf_film
            ]
        )
        return roof

    @staticmethod
    def sky_light() -> WindowThermalProperties:
        """
        Returns the thermal properties of the skylights situated on the roof.
        """
        properties = WindowThermalProperties(
            ID='sky_light',
            U=Q_(1.6, 'W / (m ** 2 * K)'),
            SHGC_cog_dir={
                0.0: 0.4,
                40.0: 0.4,
                50.0: 0.4,
                60.0: 0.4,
                70.0: 0.4,
                80.0: 0.4
            },
            SHGC_cog_dif=0.4,
            SHGC_wnd=0.4
        )
        return properties


class Construction:
    """
    Class for creating the building construction, and adding it to the
    single-zone building.
    """
    light_wall: ConstructionAssembly
    heavy_wall: ConstructionAssembly
    roof: ConstructionAssembly

    @classmethod
    def create_construction_assemblies(
        cls,
        T_int: Quantity,
        T_ext: Quantity
    ) -> None:
        """
        Creates the construction assemblies of the space.

        Parameters
        ----------
        T_int:
            Interior temperature.
        T_ext:
            Exterior temperature.
        """
        cls.light_wall = ConstructionAssemblies.exterior_wall_light(
            T_ext=T_ext,
            T_int=T_int,
            T_asp=Q_(32.2, 'degC'),
            dT_asp=Q_(5.6, 'K'),
            v_wind=Q_(3.4, 'm / s'),
            t_ins=Q_(140, 'mm')
        )

        cls.heavy_wall = ConstructionAssemblies.exterior_wall_heavy(
            T_ext=T_ext,
            T_int=T_int,
            v_wind=Q_(3.4, 'm / s'),
            t_ins=Q_(140, 'mm')
        )

        cls.roof = ConstructionAssemblies.roof(
            T_ext=T_ext,
            T_int=T_int,
            v_wind=Q_(3.4, 'm / s'),
            t_ins=Q_(169, 'mm'),
            heat_flow_dir=HeatFlowDirection.DOWNWARDS
        )

    @classmethod
    def add(cls, space: Space, is_heavy: bool = False) -> None:
        """
        Adds the building construction to the space.

        With boolean `is_heavy` a choice can be made between a heavy-weight
        wall construction (concrete exterior walls) or a light-weight wall
        construction.
        """
        if is_heavy:
            wall = cls.heavy_wall
        else:
            wall = cls.light_wall

        cls._add_north_wall(space, wall)

        cls._add_west_wall(space, wall)

        cls._add_east_wall(space, wall)

        cls._add_roof(space, cls.roof)

        cls._add_thermal_mass(space)

    @staticmethod
    def _add_north_wall(
        space: Space,
        constr_assem: ConstructionAssembly
    ) -> None:
        """
        Adds the north wall to the space.
        """
        space.add_ext_building_element(
            ID='north_wall',
            azimuth=Q_(0, 'deg'),
            tilt=Q_(90.0, 'deg'),
            width=Q_(18.68, 'm'),
            height=Q_(6.0, 'm'),
            construction_assembly=constr_assem,
            surface_color='light-colored'
        )

    @staticmethod
    def _add_west_wall(
        space: Space,
        constr_assem: ConstructionAssembly
    ) -> None:
        """
        Adds the west wall to the space.
        """
        space.add_ext_building_element(
            ID='west_wall',
            azimuth=Q_(270, 'deg'),
            tilt=Q_(90, 'deg'),
            width=Q_(1.5 * 18.68, 'm'),
            height=Q_(6.0, 'm'),
            construction_assembly=constr_assem,
            surface_color='light-colored'
        )

    @staticmethod
    def _add_east_wall(
        space: Space,
        constr_assem: ConstructionAssembly
    ) -> None:
        """
        Adds the east wall to the space.
        """
        space.add_ext_building_element(
            ID='east_wall',
            azimuth=Q_(90, 'deg'),
            tilt=Q_(90, 'deg'),
            width=Q_(1.5 * 18.68, 'm'),
            height=Q_(6.0, 'm'),
            construction_assembly=constr_assem,
            surface_color='light-colored'
        )

    @staticmethod
    def _add_roof(
        space: Space,
        constr_assem: ConstructionAssembly
    ) -> None:
        """
        Adds the roof to the space.
        """
        roof = space.add_ext_building_element(
            ID='roof',
            azimuth=Q_(0, 'deg'),
            tilt=Q_(0, 'deg'),
            width=Q_(18.68, 'm'),
            height=Q_(1.5 * 18.68, 'm'),
            construction_assembly=constr_assem,
            surface_color='dark-colored'
        )

        # Add skylight 1:
        roof.add_window(
            ID='sky_light_1',
            width=Q_(3, 'm'),
            height=Q_(10, 'm'),
            therm_props=ConstructionAssemblies.sky_light(),
        )

        # Add skylight 2:
        roof.add_window(
            ID='sky_light_2',
            width=Q_(3, 'm'),
            height=Q_(10, 'm'),
            therm_props=ConstructionAssemblies.sky_light(),
        )

    @staticmethod
    def _add_thermal_mass(space: Space) -> None:
        """
        Adds the interior thermal mass to the space.
        """
        space.add_internal_thermal_mass(
            A=Q_(348.81, 'm ** 2'),
            R=Q_(0.015, 'm ** 2 * K / W'),
            C=Q_(300, 'kJ / (m ** 2 * K)')
        )
    

class ExpositionHall:
    """
    Class that models the single-zone exposition hall.
    """
    @classmethod
    def create(
        cls,
        climate: ClimateData,
        cooling_on_period: tuple[int, int] = (0, 24),
        T_comfort: Quantity = Q_(26, 'degC'),
        T_economy: Quantity = Q_(26, 'degC'),
        comfort_period: tuple[int, int] = (8, 18),
        max_num_people: int = 200,
        min_num_people: int = 100,
        occupancy_period: tuple[int, int] = (8, 18),
        is_heavy_construction: bool = False
    ) -> Space:
        """
        Creates the building and returns its single space.
        """

        # Create a time schedule for turning the cooling system on/off:
        cooling_schedule = cls._create_cooling_schedule(cooling_on_period)

        # Create a time schedule to change the setpoint of the interior
        # temperature:
        space_temperature_schedule = cls._create_space_temperature_schedule(
            T_comfort,
            T_economy,
            comfort_period
        )

        # Create the internal heat gains inside the building:
        internal_heat_gains = cls._create_internal_heat_gains(
            max_num_people,
            min_num_people,
            occupancy_period
        )

        # Create the single space of the building:
        space = cls._create_single_space(
            climate,
            space_temperature_schedule,
            cooling_schedule,
            internal_heat_gains,
            is_heavy_construction
        )
        return space

    @staticmethod
    def _create_single_space(
        climate: ClimateData,
        space_temperature_schedule: TemperatureSchedule,
        cooling_schedule: OnOffSchedule | None,
        internal_heat_gains: list[InternalHeatGain],
        is_heavy_construction: bool = False
    ) -> Space:
        """
        Creates and configures the building hierarchy and returns the single
        space of the building.
        """
        # Create the space:
        space = Space.create(
            ID='exposition_hall',
            height=Q_(6.0, 'm'),
            length=Q_(1.5 * 18.68, 'm'),
            width=Q_(18.68, 'm'),
            climate_data=climate,
            T_int_fun=space_temperature_schedule,
            cooling_schedule=cooling_schedule,
        )

        # Add the building construction to the space:
        Construction.create_construction_assemblies(
            T_int=space_temperature_schedule.base_value,
            T_ext=climate.Tdb_avg
        )
        Construction.add(space, is_heavy=is_heavy_construction)

        # Add the internal heat gains to the space:
        for ihg in internal_heat_gains:
            space.add_internal_heat_gain(ihg)

        # Create a ventilation zone, and add the space to this zone:
        vz = VentilationZone.create(ID='exposition_hall')
        vz.add_space(space)

        # Configure the ventilation characteristics of the space (using the
        # default values):
        space.configure_ventilation()

        # Create a building entity, and add the ventilation zone to this
        # building entity:
        be = BuildingEntity.create(ID='exposition_hall')
        be.add_ventilation_zone(vz)

        # Create a building, and add the building entity to this building:
        bu = Building.create(ID='exposition_hall')
        bu.add_building_entity(be)

        # Only return the single space of the building:
        return space
   
    @staticmethod
    def _create_space_temperature_schedule(
        T_comfort: Quantity,
        T_economy: Quantity,
        comfort_period: tuple[int, int]
    ) -> TemperatureSchedule:
        """
        Creates a time schedule for setpoint changes of the space air
        temperature.

        Between the start and the end hour of the comfort period, the space air
        temperature setpoint is set to the value of `T_comfort`. During the
        other hours of the day, the setpoint is set to the value of `T_economy`.
        """
        # Create a temperature schedule with a base value of `T_economy`:
        schedule = TemperatureSchedule.create(
            ID='space_temperature_schedule',
            base_value=T_economy
        )

        # Change the setpoint to `T_comfort` during the `comfort_period`:
        for t in range(comfort_period[0], comfort_period[1] + 1):
            schedule.set_value(t, T_comfort)

        return schedule

    @staticmethod
    def _create_cooling_schedule(
        cooling_on_period: tuple[int, int]
    ) -> OnOffSchedule:
        """
        Creates a time schedule for turning the cooling system on or off.

        Between the start and the end hour of the cooling period, the cooling
        system is on. During the other hours of the day, the cooling system is
        off.
        """
        schedule = OnOffSchedule.create(
            ID='cooling_schedule',
            base_value=False
        )

        for hour in range(cooling_on_period[0], cooling_on_period[1] + 1):
            schedule.set_value(hour, True)

        return schedule

    @staticmethod
    def _create_internal_heat_gains(
        max_num_people: int,
        min_num_people: int,
        occupancy_period: tuple[int, int]
    ) -> list[InternalHeatGain]:
        """
        Creates the internal heat gains in the space.

        Only internal heat gain by people is considered.

        Between the start and end hour of the occupancy period, the number of
        people is equal to `max_num_people`. During the other hours of the day,
        the number of people in the space is equal to `min_num_people`.
        """
        occupancy_schedule = OccupancySchedule.create(
            ID='occupancy_schedule',
            base_value=min_num_people
        )

        for hour in range(occupancy_period[0], occupancy_period[1] + 1):
            occupancy_schedule.set_value(hour, max_num_people)

        people = PeopleHeatGain.create(
            ID='people',
            Q_sen_person=Q_(75, 'W'),
            Q_lat_person=Q_(55, 'W'),
            F_rad=Q_(58, 'pct'),
            schedule=occupancy_schedule
        )
        return [people]


def main():
    # Set the location and the climate design data:
    climate = ClimateData.create_from_ASHRAE_weather_data(
        location=Location(
            name='Ghent',
            lat=Q_(51.183, 'deg'),
            lon=Q_(3.8, 'deg'),
            alt=Q_(8.0, 'm'),
            tz='Europe/Brussels'
        ),
        design_day=date(2022, 7, 21),
        Tdb_avg=Q_(26.7, 'degC'),
        Tdb_range=Q_(11.3, 'K'),
        Twb_mc=Q_(19.2, 'degC'),
        tau_beam=0.426,
        tau_dif=2.247
    )

    # Create the single-zone building:
    hall = ExpositionHall.create(
        climate,
        cooling_on_period=(0, 24),
        T_comfort=Q_(26, 'degC'),
        T_economy=Q_(26, 'degC'),
        comfort_period=(8, 17),
        max_num_people=200,
        min_num_people=100,
        occupancy_period=(8, 17),
        is_heavy_construction=False
    )

    # Display a table of the heat gains and the cooling loads on an hourly basis:
    Q_gains = hall.get_heat_gains(unit='kW')
    with pd.option_context('display.width', None):
        print(Q_gains)

    print(
        "Maximum sensible cooling load = "
        f"{Q_gains['Q_sen_load'].max():.3f} kW "
        f"({Q_gains['Q_sen_load'].idxmax()})",
        "Maximum latent cooling load = "
        f"{Q_gains['Q_lat_load'].max():.3f} kW "
        f"({Q_gains['Q_lat_load'].idxmax()})",
        "Maximum total cooling load = "
        f"{Q_gains['Q_tot_load'].max():.3f} kW "
        f"({Q_gains['Q_tot_load'].idxmax()})",
        sep='\n', end='\n\n'
    )

    # Display a diagram of the hourly cooling load and the time course of the
    # indoor air temperature:
    T_int_df = hall.get_space_air_temperatures()

    chart = LineChart()
    chart.add_y2_axis()
    chart.add_xy_data(
        label='cooling load',
        x1_values=[time.hour for time in Q_gains['time']],
        y1_values=Q_gains['Q_tot_load']
    )
    chart.add_xy_data(
        label='space air temperature',
        x1_values=[time.hour for time in Q_gains['time']],
        y2_values=T_int_df['T_int'],
        style_props={'color': 'orange'}
    )
    chart.x1.add_title('hour of the day')
    chart.x1.scale(0, 24, 1)
    chart.y1.add_title('cooling load, W')
    chart.y1.scale(0, 75, 5)
    chart.y2.add_title('space air temperature, °C')
    chart.y2.scale(0, 35, 5)
    chart.show()

    # Show a table of the heat flows into and out from the interior thermal
    # mass:
    Q_stor = hall.get_thermal_storage_heat_flows(Q_unit='kW')
    with pd.option_context('display.width', None):
        print(Q_stor)

    # Show a diagram of the hourly dry-bulb outdoor air temperature during the
    # cooling design day:
    chart2 = LineChart()
    chart2.add_xy_data(
        label='dry-bulb outdoor air temperature',
        x1_values=[time.hour for time in climate.Tdb_profile['t']],
        y1_values=[Tdb.to('degC').m for Tdb in climate.Tdb_profile['T']]
    )
    chart2.x1.add_title('hour of the day')
    chart2.x1.scale(0, 24, 1)
    chart2.y1.add_title('dry-bulb outdoor air temperature, °C')
    chart2.show()


if __name__ == '__main__':
    main()
