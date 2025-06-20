import random
import csv
from io import StringIO

SIMULATION_DURATION = 100
MIN_SERVICE_TIME = 5
MAX_SERVICE_TIME = 15
FUELS = ["A", "B"]
FUELS_PROBABILITY = [0.7, 0.3]
# CAR_ARRIVAL_INTERVAL = (1, 3)
NORMAL_ARRIVAL_MEAN = 2  # Średni czas przyjazdu samochodu
NORMAL_ARRIVAL_STD = 0.5  # Odchylenie standardowe
QUEUE_MAX_SIZE = 12
DISPENSER_QUEUE_MAX_SIZE = 3

DISPENSERS_CONFIG = [
    {"id": 0, "fuels": {"A"}},
    {"id": 1, "fuels": {"A"}},
    {"id": 2, "fuels": {"B", "A"}},
    {"id": 3, "fuels": {"B"}},
]

config = {
    "simulation_duration": SIMULATION_DURATION,
    "min_service_time": MIN_SERVICE_TIME,
    "max_service_time": MAX_SERVICE_TIME,
    "fuels": FUELS,
    "fuels_probability": FUELS_PROBABILITY,
    # "car_arrival_interval": CAR_ARRIVAL_INTERVAL,
    "normal_arrival_mean": NORMAL_ARRIVAL_MEAN,
    "normal_arrival_std": NORMAL_ARRIVAL_STD,
    "queue_max_size": QUEUE_MAX_SIZE,
    "dispenser_queue_max_size": DISPENSER_QUEUE_MAX_SIZE,
    "dispensers_config": DISPENSERS_CONFIG,
}


class Car:
    def __init__(self, id: int, fuel_type: str, service_time: int):
        self.id = id
        self.fuel_type = fuel_type
        self.service_time = service_time
        self.waiting_time = 0

    def wait(self):
        self.waiting_time += 1

    def get_waiting_time(self):
        return self.waiting_time

    def to_dict(self):
        return {
            "id": self.id,
            "fuel_type": self.fuel_type,
            "service_time": self.service_time,
        }


class Dispenser:
    def __init__(self, id: int, fuels: set):
        self.id = id
        self.fuels = fuels
        self.car_inside = None
        self.is_available = True
        self.expected_finish_time = -1
        self.dispenser_queue = []
        self.serviced_cars = 0

    def start_service(self, car: Car, timer: int):
        self.is_available = False
        self.car_inside = car
        self.expected_finish_time = timer + car.service_time

    def end_service(self):
        self.is_available = True
        self.car_inside = None
        self.expected_finish_time = -1
        self.serviced_cars += 1

    def to_dict(self):
        return {
            "id": self.id,
            "fuels": list(self.fuels),
            "is_available": self.is_available,
            "car_inside": self.car_inside.to_dict() if self.car_inside else None,
            "expected_finish_time": self.expected_finish_time,
            "mini_queue": [car.to_dict() for car in self.dispenser_queue],
        }


class Event:
    time: int
    dispenser_id: int
    car_id: int

    def __init__(self, time, dispenser_id, car_id):
        self.time = time
        self.dispenser_id = dispenser_id
        self.car_id = car_id

    def __str__(self):
        return f"Event(time={self.time}, dispenser_id={self.dispenser_id}, car_id={self.car_id})"

    def to_dict(self):
        return {
            "time": self.time,
            "dispenser_id": self.dispenser_id,
            "car_id": self.car_id,
        }


def car_generator():
    car_counter = 0
    while True:
        car_counter += 1
        fuel_type = random.choices(FUELS, weights=FUELS_PROBABILITY, k=1)[0]
        service_time = random.randint(MIN_SERVICE_TIME, MAX_SERVICE_TIME)

        yield Car(id=car_counter, fuel_type=fuel_type, service_time=service_time)


def choose_dispenser(car: Car, dispensers: list[Dispenser]):
    """
    Wybór dystrybutora z najkrótszą kolejką i odpowiednim paliwem.
    """
    available_dispensers = [
        d
        for d in dispensers
        if car.fuel_type in d.fuels
        and len(d.dispenser_queue) < DISPENSER_QUEUE_MAX_SIZE
    ]
    if available_dispensers:
        available_dispensers.sort(key=lambda d: len(d.dispenser_queue))
        return available_dispensers[0]
    return None


def choose_dispenser_with_mistake(car: Car, dispensers: list[Dispenser]):
    """
    Wybór dystrybutora z nakrótszą kolejką, ale z prawdopodobieńswem pomylenia typu paliwa
    """
    mistake_chance = 0.1
    available_dispensers = [
        d for d in dispensers if len(d.dispenser_queue) < DISPENSER_QUEUE_MAX_SIZE
    ]
    if available_dispensers:
        if random.random() < mistake_chance:
            # Pomyłka kierowcy, wybiera dystrybutor z innym paliwem
            wrong_fuel = random.choice([f for f in FUELS if f != car.fuel_type])
            dispensers_with_wrong_fuel = [
                d for d in available_dispensers if wrong_fuel in d.fuels
            ]
            if dispensers_with_wrong_fuel:
                dispensers_with_wrong_fuel.sort(key=lambda d: len(d.dispenser_queue))
                return dispensers_with_wrong_fuel[0]
        else:
            return choose_dispenser(car, dispensers)


def cars_waiting(queue: list[Car], dispensers: list[Dispenser]):
    for car in queue:
        car.wait()

    for dispenser in dispensers:
        for car in dispenser.dispenser_queue:
            car.wait()


def run_simulation():
    current_time = 0
    dispensers = [Dispenser(**config) for config in DISPENSERS_CONFIG]
    queue = []
    events = []
    simulation_states = []

    stats = {
        "avg_waiting_time": 0,
        "time_when_first_car_at_main_queue": 0,
        "time_when_first_car_at_mini_queue": 0,
        "total_cars_serviced": 0,
        "total_cars_generated": 0,
        "cars_serviced_by_dispenser": {d.id: 0 for d in dispensers},
        "total_cars_in_main_queue_at_end": 0,
        "total_cars_in_mini_queues_at_end": 0,
        "time_when_queue_is_full": 0,
        "total_cars_with_fuel": {f: 0 for f in FUELS},
        "number_of_mistakes": 0,
    }

    car_gen = car_generator()

    # next_car_arrival = current_time + random.randint(*CAR_ARRIVAL_INTERVAL)
    
    # Rozkład normalny dla przyjazdu samochodów
    next_car_arrival = current_time + max(
        1,
        int(random.normalvariate(NORMAL_ARRIVAL_MEAN, NORMAL_ARRIVAL_STD)),
    )
    # stats ----
    car_counter = 0
    car_serviced_counter = 0
    total_waiting_time = 0
    cars_with_fuel = {f: 0 for f in FUELS}
    # -----------

    while current_time <= SIMULATION_DURATION:

        # Zapis stanu symulacji (dla frontendu)
        simulation_states.append(
            {
                "time": current_time,
                "dispensers": [d.to_dict() for d in dispensers],
                "main_queue": [c.to_dict() for c in queue],
            }
        )

        # Przyjazd samochodu
        if current_time >= next_car_arrival:
            car = next(car_gen)
            car_counter += 1
            cars_with_fuel[car.fuel_type] += 1
            queue.append(car)


            # Opcjonalnie: jeśli kolejka jest pełna, samochód odjeżdża
            # if len(queue) < QUEUE_MAX_SIZE:
            # queue.append(car)
            # else:
            # print(f"Samochód {car.id} odjechał, kolejka pełna.")
            # next_car_arrival = current_time + random.randint(*CAR_ARRIVAL_INTERVAL)
            
            next_interval = max(1, int(random.normalvariate(NORMAL_ARRIVAL_MEAN, NORMAL_ARRIVAL_STD)))
            next_car_arrival = current_time + next_interval
        car = queue[0] if queue else None

        if car:

            # chosen_dispenser = choose_dispenser(car, dispensers)
            chosen_dispenser = choose_dispenser_with_mistake(car, dispensers)

            # Sampchód wchodzi do najkrótszej kolejki dystrybutora (jeśli jest dostępny)
            if chosen_dispenser:
                chosen_dispenser.dispenser_queue.append(car)
                queue.pop(0)
            else:
                if stats["time_when_first_car_at_main_queue"] == 0:
                    stats["time_when_first_car_at_main_queue"] = current_time

        for dispenser in dispensers:

            # Dodawanie auta do indywidualnej kolejki dystrybutora
            if dispenser.is_available and dispenser.dispenser_queue:
                car = dispenser.dispenser_queue[0]
                if car.fuel_type in dispenser.fuels:
                    dispenser.dispenser_queue.pop(0)
                    total_waiting_time += car.get_waiting_time()

                    # print(
                    #     f"Dispenser {dispenser.id} is available for car {car.id} with fuel {car.fuel_type}"
                    # )

                    dispenser.start_service(car, current_time)
                    events.append(Event(current_time, dispenser.id, car.id))
                else:
                    # kierowca się pomylił i wraca na koniec kolejki
                    queue.append(car)
                    dispenser.dispenser_queue.pop(0)
                    stats["number_of_mistakes"] += 1

                    # print(
                    #     f"Car {car.id} made a mistake and returned to the main queue."
                    # )
            else:
                if (
                    dispenser.car_inside
                    and current_time >= dispenser.expected_finish_time
                ):
                    # print(
                    #     f"Dispenser {dispenser.id} finished servicing car {dispenser.car_inside.id}"
                    # )
                    dispenser.end_service()
                    car_serviced_counter += 1

        cars_waiting(queue, dispensers)
        current_time += 1

    stats["total_cars_serviced"] = car_serviced_counter
    stats["total_cars_generated"] = car_counter
    stats["total_cars_in_main_queue_at_end"] = len(queue)
    stats["total_cars_in_mini_queues_at_end"] = sum(
        len(d.dispenser_queue) for d in dispensers
    )
    stats["cars_serviced_by_dispenser"] = {d.id: d.serviced_cars for d in dispensers}
    stats["total_cars_with_fuel"] = cars_with_fuel
    stats["avg_waiting_time"] = (
        total_waiting_time / car_serviced_counter if car_serviced_counter > 0 else 0
    )

    return simulation_states, stats


def multiple_stats_to_csv(stats: list[dict]):

    output = StringIO()
    writer = csv.writer(output)
    keys = stats[0].keys()
    headers = []

    for key in keys:
        if isinstance(stats[0][key], dict):
            headers.extend([f"{key}_{sub_key}" for sub_key in stats[0][key].keys()])
        else:
            headers.append(key)

    writer.writerow(headers)

    for row in stats:
        values = []
        for value in row.values():
            if isinstance(value, dict):
                for sub_key in value.keys():
                    values.append(value[sub_key])
            else:
                values.append(value)
        writer.writerow(values)
    return output.getvalue()


def export_multiple_stats_to_csv(stats: list[dict], filename: str):

    csv_data = multiple_stats_to_csv(stats)
    with open(filename, "w", newline="") as file:
        file.write(csv_data)


def run_multiple_simulations(n: int):
    all_states = []
    all_stats = []

    for i in range(n):
        states, stats = run_simulation()
        all_states.append(states)
        all_stats.append(stats)

    return all_states, all_stats


def show_config():
    print("Current configuration:")
    for key, value in config.items():
        print(f"{key}: {value}")


if "__main__" == __name__:

    show_config()
    simulation_states, simulation_stats = run_multiple_simulations(100)
    export_multiple_stats_to_csv(simulation_stats, "simulation_stats.csv")
    print("Simulation completed and stats exported to 'simulation_stats.csv'.")
