import math
import random

def rewrite_code_to_python():
    # Получаем все элементы дорог по их ID
    road_elements = {
        'a': 'element_a', # document.getElementById('a'),  // Placeholder for DOM element
        'A': 'element_A', # document.getElementById('A'),  // Placeholder for DOM element
        'b': 'element_b', # document.getElementById('b'),  // Placeholder for DOM element
        'B': 'element_B', # document.getElementById('B'),  // Placeholder for DOM element
        'sn': 'element_sn_bridge', # document.getElementById('sn-bridge'), // Placeholder for DOM element
        'ns': 'element_ns_bridge'  # document.getElementById('ns-bridge')  // Placeholder for DOM element
    }

    # Вычисляем и выводим длины
    print('Длины участков дорог:')
    for name, element in road_elements.items():
        if element: # In Python, just check if element is not None or empty string
            # Simulate getTotalLength() - Assuming it returns a numerical length
            length = math.floor(100 + random.random() * 200) # Placeholder for element.getTotalLength() simulation
            print(f"{name}: {length}px")
        else:
            print(f"Элемент {name} не найден!")

    xmlns = "http://www.w3.org/2000/svg"
    frame = "the_coordinate_frame" # document.getElementById("the-coordinate-frame") # Placeholder for DOM element


    # event handlers and pointers to DOM elements
    sn_bridge = 'sn_bridge_element' # document.getElementById("sn-bridge") # Placeholder for DOM element
    ns_bridge = 'ns_bridge_element' # document.getElementById("ns-bridge") # Placeholder for DOM element
    the_barricade = 'the_barricade_element' # document.getElementById("barricade") # Placeholder for DOM element
    go_button = 'go_button_element' # document.getElementById("the-run-button") # Placeholder for DOM element
    reset_button = 'reset_button_element' # document.getElementById("the-reset-button") # Placeholder for DOM element
    max_cars_input = 'max_cars_input_element' # document.getElementById("max-cars-input") # Placeholder for DOM element
    launch_rate_slider = 'launch_rate_slider_element' # document.getElementById("launch-rate-slider") # Placeholder for DOM element
    launch_rate_output = 'launch_rate_output_element' # document.getElementById("launch-rate-output") # Placeholder for DOM element
    congestion_slider = 'congestion_slider_element' # document.getElementById("congestion-slider") # Placeholder for DOM element
    congestion_output = 'congestion_output_element' # document.getElementById("congestion-output") # Placeholder for DOM element
    launch_timing_menu = 'launch_timing_menu_element' # document.getElementById("launch-timing-menu") # Placeholder for DOM element
    routing_mode_menu = 'routing_mode_menu_element' # document.getElementById("routing-mode-menu") # Placeholder for DOM element
    speed_menu = 'speed_menu_element' # document.getElementById("speed-menu") # Placeholder for DOM element
    selection_method_menu = 'selection_method_menu_element' # document.getElementById("selection-method-menu") # Placeholder for DOM element
    geek_toggle = 'geek_toggle_element' # document.getElementById("geek-out") # Placeholder for DOM element
    hint_toggle = 'hint_toggle_element' # document.getElementById("hint-toggle") # Placeholder for DOM element
    hint_stylesheet = 'hint_stylesheet_element' # document.getElementById("hint-stylesheet") # Placeholder for DOM element


    # globals
    model_state = "stopped" # other states are "running" and "stopping"
    bridge_blocked = True
    routing_mode = "selfish" # other mode is "random"
    speed_mode = "theoretical" # alternatives are "actual," "historical"
    selection_method = "minimum" # other choice is "weighted-probability"
    launch_timing = "poisson" # others are "uniform," "periodic"
    # launch_timer = poisson # pointer to function, will be reassigned
    global_clock = 0 # integer count of simulation steps, for measuring travel time
    next_departure = 0 # next clock reading at which a car is due to depart
    max_cars = float('inf') # specified by the macCarsInput element; if blank, no limit
    animation_timer = None # for setInterval/clearInterval
    car_radius = 3
    car_length = 2 * car_radius
    total_path_length = 1620
    car_queue_size = (total_path_length / car_length) + 10 # make sure we never run out of cars
    car_array = [None] * car_queue_size # retain pointers to all cars, so we can loop through them
    speed_limit = 3 # distance per time step in free-flowing traffic
    launch_rate = 0.55 # rate at which cars attempt to enter the network at Origin; exact meaning depends on launchTiming
    congestion_coef = 0.55 # 0 means no congestion slowing at all; 1 means max density, traffic slows almost to a stop
    quickest_trip = 582 / speed_limit # Minimum number of time steps to traverse shortest route with zero congestion
    geek_mode = False # whether to show extra geeky controls; initially no
    hint_mode = True # whether to show tooltips; intially yes

    # my globals
    num_of_steps = 0


    # probability distributions and related stuff

    def coin_flip():
        return random.random() < 0.5 # note: returns boolean

    # Return a random interval drawn from exponential distribution
    # with rate parameter lambda
    # Why 1 - Math.random() rather than just plain Math.random()?
    # So that we get (0,1] instead of [0, 1), thereby avoiding the
    # risk of taking log(0).
    # The parameter lambda, which determines the intensity of the
    # Poisson process, will be given a value of launchRate/speedLimit,
    # which ranges from 0 to 1/3.
    def poisson(lambda_val):
        return -math.log(1 - random.random()) / lambda_val

    # Return a real chosen uniformly at random from a finite interval [0, d),
    # where d = 2 / lambda. Thus the mean of the distribution is 1 / lambda.
    def uniform(lambda_val):
        return random.random() * 2 / lambda_val

    # Generates a simple periodic sequence, without randomness, with period
    # 1 / lambda. But note that cars are launched only at integer instants,
    # so the observed stream of cars may not be as regular as this function
    # would suggest.
    def periodic(lambda_val):
        return 1 / lambda_val


    # The road network is built from two kinds of components: nodes, where
    # roads begin or end of intersect, and links, which are directed paths running
    # from one node to the next.

    # Most of the logic in the model is implemented by the nodes, which
    # act as routers for the cars. Visually, a node is an SVG circle. Algorithmically,
    # it's a buffer with a capacity of one car.

    # constructor for Nodes
    class Node:
        def __init__(self, id_str):
            self.node_name = id_str
            self.svg_circle = id_str # document.getElementById(idStr) # visible representation // Placeholder for DOM element - use id_str for now
            # Simulate getting coords from HTML - Placeholder for DOM element property access
            self.x = 50 + random.random() * 100 # Placeholder for self.svg_circle.cx.baseVal.value
            self.y = 50 + random.random() * 100 # Placeholder for self.svg_circle.cy.baseVal.value
            self.car = None

        def has_room(self): # must call before trying to pass along a car
            return not self.car

        def accept(self, car): # no worries about atomicity; js is single-threaded
            self.car = car

        # clean up if somebody presses the reset button
        def evacuate(self):
            if self.car:
                self.car.park() # back to the parking lot
                self.car = None


        # The dispatch function is the main duty of a node -- deciding where
        # each car goes next and moving it along. Actually, there's not much
        # deciding to be done. Each car carries its own itinerary, so the node
        # merely has to consult this record and place the car on the appropriate
        # link. The itinerary takes the form of a dictionary with the structure
        # {"orig": link, "south": link, "north": link, "dest": link}, where the
        # keys are the names of nodes, and the values are links.
        def dispatch(self):
            if self.car:
                next_link_id = self.car.route.directions.get(self.node_name) # find the link where this car wants to go
                next_link = link_map.get(next_link_id) # Get Link object from link_map using link ID
                if not next_link:
                    return # Handle case where next_link is None
                if next_link.car_q.len == 0 or next_link.car_q.last().progress >= car_length: # can the link accept a car?
                    self.car.progress = 0 # recording position along the link
                    # Simulate avatar.setAttribute - Placeholder for DOM manipulation
                    # self.car.avatar.setAttribute("cx", self.x)
                    # self.car.avatar.setAttribute("cy", self.y)
                    next_link.car_q.enqueue(self.car) # send the car on its way
                    next_link.update_speed() # recalculate speed based on occupancy of link
                    self.car = None # empty buffer, ready for next


    # the four nodes of the Braess road network
    orig = Node("orig")
    dest = Node("dest")
    south = Node("south")
    north = Node("north")


    # The final destination node has some special duties, so we override
    # the dispatch method.
    class DestinationNode(Node): # Inherit from Node
        def dispatch(self): # Override dispatch method
            if self.car:
                Dashboard.record_arrival(self.car) # Dashboard is where we record stats
                self.car.park()
                self.car = None

    dest = DestinationNode("dest") # Re-assign dest to be a DestinationNode


    # Now we move on to the links, the roadways of the model. Again there's a
    # visible manifestation as an SVG element and a behind-the-scenes data
    # structure, which takes the form a queue. (See queue.js for details on
    # the latter.)
    # Note that much of the basic data about the link comes from the SVG
    # (which is defined in index.html): the length of the path, start and end
    # coordinates, which class of road it is (congestible or not).

    # constructor for links; oNode and dNode are the origin and destination nodes
    class Link:
        def __init__(self, id_str, o_node, d_node):
            self.id = id_str
            self.svg_path = id_str # document.getElementById(idStr) # Placeholder for DOM element - use id_str for now
            # Simulate getTotalLength() - Placeholder for DOM element method simulation
            self.path_length = math.floor(100 + random.random() * 200) # math.round(self.svg_path.getTotalLength())
            # console.log('Length', self.pathLength) # rounding to ensure lengths A=B and a=b
            # Simulate getPointAtLength - Placeholder for DOM element method simulation
            self.origin_xy = {'x': 0, 'y': 0} # self.svg_path.getPointAtLength(0)
            self.destination_xy = {'x': self.path_length, 'y': 0} # self.svg_path.getPointAtLength(self.pathLength)
            self.origin_node = o_node
            self.destination_node = d_node
            self.open_to_traffic = True # always true except for bridge links
            self.car_q = Queue(car_queue_size) # vehicles currently driving on this link
            # Simulate classList.contains - Placeholder for DOM element class check
            self.congestible = id_str in ["a", "b"] # self.svg_path.classList.contains("thin-road") # true for a and b only
            self.occupancy = self.car_q.len
            self.speed = speed_limit
            self.travel_time = self.path_length / speed_limit # default value, will be overridden

        def update_speed(self): # default, works for wide roads; will override for a and b
            self.speed = speed_limit
            self.travel_time = self.path_length / self.speed

        def get_car_xy(self, progress): # 0 <= progress <= path.length
            # Simulate getPointAtLength - Placeholder for DOM element method simulation
            return {'x': self.origin_xy['x'] + progress, 'y': self.origin_xy['y']} # self.svg_path.getPointAtLength(progress)


        # This is where the rubber meets the road, the procedure that actually
        # moves the cars along a link. It's also where most of the CPU cycles
        # get spent.
        # The basic idea is to take a car's current speed, determine how far it
        # will move along the path at that speed in one time step, and update
        # its xy coordinates. But there's a complication: The car may not be able
        # to move that far if there's another car in front of it.
        # The first car in the queue needs special treatment. We know there's
        # no one in front of it, but it may be near the end of the path.
        def drive(self):
            if self.car_q.len > 0:
                first_car = self.car_q.peek(0)
                first_car.past_progress = first_car.progress
                first_car.progress = min(self.path_length, first_car.progress + self.speed) # don't go off the end
                first_car.odometer += first_car.progress - first_car.past_progress # cumulative distance over whole route
                car_xy = self.get_car_xy(first_car.progress)
                # Simulate avatar.setAttribute - Placeholder for DOM manipulation
                # firstCar.avatar.setAttribute("cx", carXY.x) # setting SVG coords
                # firstCar.avatar.setAttribute("cy", carXY.y)

                for i in range(1, self.car_q.len): # now for all the cars after the first one
                    leader = self.car_q.peek(i - 1)
                    follower = self.car_q.peek(i)
                    follower.past_progress = follower.progress
                    follower.progress = min(follower.progress + self.speed, leader.progress - car_length) # don't rear-end the leader
                    follower.odometer += follower.progress - follower.past_progress
                    car_xy = self.get_car_xy(follower.progress)
                    # Simulate avatar.setAttribute - Placeholder for DOM manipulation
                    # follower.avatar.setAttribute("cx", carXY.x)
                    # follower.avatar.setAttribute("cy", carXY.y)

                if first_car.progress >= self.path_length and self.destination_node.has_room(): # hand off car to destination node
                    self.destination_node.accept(self.car_q.dequeue())
                    self.update_speed() # occupancy has decreased by 1


        # when Reset pressed, dump all the cars back to the parking lot
        def evacuate(self):
            while self.car_q.len > 0:
                c = self.car_q.dequeue()
                c.park()
            self.update_speed()


    # here we create the six links of the road network
    a_link = Link("a", orig, south)
    a_link_id = "a" # Store ID for lookup
    a_link_name = "aLink" # Store name for lookup
    a_link_js_name = "aLink" # Store original JS name for potential future reference

    a_link_map = {"a": a_link}

    A_link = Link("A", orig, north)
    a_link_map["A"] = A_link # Add to link_map
    A_link_id = "A"
    A_link_name = "ALink"
    A_link_js_name = "ALink"

    b_link = Link("b", north, dest)
    a_link_map["b"] = b_link # Add to link_map
    b_link_id = "b"
    b_link_name = "bLink"
    b_link_js_name = "bLink"

    B_link = Link("B", south, dest)
    a_link_map["B"] = B_link # Add to link_map
    B_link_id = "B"
    B_link_name = "BLink"
    B_link_js_name = "BLink"

    sn_link = Link("sn-bridge", south, north)
    a_link_map["sn-bridge"] = sn_link # Add to link_map
    sn_link_id = "sn-bridge"
    sn_link_name = "SnLink"
    sn_link_js_name = "snLink"

    ns_link = Link("ns-bridge", north, south)
    a_link_map["ns-bridge"] = ns_link # Add to link_map
    ns_link_id = "ns-bridge"
    ns_link_name = "NsLink"
    ns_link_js_name = "nsLink"

    link_map = a_link_map # Rename the map to follow snake_case

    # default state, bridge closed in both directions
    sn_link.open_to_traffic = False
    ns_link.open_to_traffic = False

    # We need to override the updateSpeed method for the narrow links a and b,
    # where traffic slows as a function of density. Under the formula given here,
    # if occupancy === 0 (i.e., no cars on the road), speed === speedLimit. At
    # maximum occupancy and congestionCoef === 1, speed falls to 0 and travelTime
    # diverges. The if stmt makes sure speed is always strictly positive.
    def a_link_update_speed(): # Define as function as direct method override is less common in Python, can be a method in Link class if preferred.
        epsilon = 1e-10
        a_link.occupancy = a_link.car_q.len
        a_link.speed = speed_limit - (a_link.occupancy * car_length * speed_limit * congestion_coef) / a_link.path_length
        if a_link.speed <= 0:
            a_link.speed = epsilon
        a_link.travel_time = a_link.path_length / a_link.speed

    a_link.update_speed = a_link_update_speed # Assign function as method

    # borrow the aLink method for bLink
    b_link.update_speed = a_link.update_speed # Assign function as method (already defined above)


    # The following four method overrides are for efficiency only. They
    # can be eliminated without changing functionality.
    # The default getCarXY uses the SVG path method getPointAtLength.
    # Profiling suggests that the program spends most of its cpu cycles
    # executing this function. Four of the links are axis-parallel straight
    # lines, for which we can easily calculate position without going into
    # the SVG path.
    def a_link_get_car_xy(progress):
        y = a_link.origin_xy['y']
        x = a_link.origin_xy['x'] + progress
        return {'x': x, 'y': y} # return a point object in same format as getPointAtLength

    a_link.get_car_xy = a_link_get_car_xy # Assign function as method

    b_link.get_car_xy = a_link.get_car_xy # again bLink borrows the method

    def sn_link_get_car_xy(progress):
        x = sn_link.origin_xy['x']
        y = sn_link.origin_xy['y'] + progress
        return {'x': x, 'y': y}

    sn_link.get_car_xy = sn_link_get_car_xy # Assign function as method

    def ns_link_get_car_xy(progress): # borrowing won't work in this case because of sign difference
        x = ns_link.origin_xy['x']
        y = ns_link.origin_xy['y'] - progress
        return {'x': x, 'y': y}

    ns_link.get_car_xy = ns_link_get_car_xy # Assign function as method


    # this one is not a link, just a bare queue, but
    # it has a closely analogous function. This is the holding
    # pen for cars after they reach the destination and before
    # they get recycled to the origin.
    parking_lot = Queue(car_queue_size) # holds idle cars


    # A Route object encodes a sequence of links leading from Origin
    # to Destination. For the road network in this model, there are
    # just two possible routes when the bridge is closed, four when
    # it is open. Each of these routes has an associated color; the
    # cars following the route display the color. And the route
    # also includes a directions object that instructs each node
    # on how to handle a car following the route.

    # constructor
    class Route:
        def __init__(self):
            self.label = ""
            self.paint_color = None
            self.directions = {"orig": None, "south": None, "north": None, "dest": None}
            self.itinerary = []
            self.route_length = 0
            self.travel_time = 0

        # total length is just sum of constituent link lengths
        def calc_route_length(self):
            rtl = 0
            for link_id in self.itinerary: # Iterate through link IDs in itinerary
                link_obj = link_map.get(link_id) # Get Link object from link_map
                if link_obj: # Check if link_obj is not None
                    rtl += link_obj.path_length
            self.route_length = rtl


        # For calculating the expected travel time over a route, we have a
        # choice of three procedures. (The choice is determined by the
        # Speed Measurement selector.)

        def calc_travel_time(self):
            if speed_mode == "theoretical":
                self.calc_travel_time_theoretical()
            elif speed_mode == "actual":
                self.calc_travel_time_actual()
            else:
                self.calc_travel_time_historical()


        # The theoretical travel time comes straight out of the definition
        # of the model. For links a and b travel time is a function of
        # occupancy -- the number of cars traversing the link. All other
        # links have travel time proportional to their length, regardless
        # of traffic density. Thus we can just add up these numbers for
        # the links composing a route.
        # Why is this value "theoretical"? It assumes that cars always
        # travel at the speed limit on all non-congestible links. But in
        # there may be delays getting onto and off of those links, causing
        # "queue spillback" and increasing the travel time. Calculations
        # based on theretical values may therefore underestimate the true
        # travel time.
        def calc_travel_time_theoretical(self):
            tt = 0
            for link_id in self.itinerary: # Iterate through link IDs in itinerary
                link_obj = link_map.get(link_id) # Get Link object from link_map
                if link_obj: # Check if link_obj is not None
                    tt += link_obj.travel_time
            self.travel_time = tt

        # An alternative to the theoretical approach is to actually measure
        # the speed of cars currently traversing the route, and take an
        # average.
        # TODO: I had a reason for looping through all cars, rather than
        # just those on the route (using queue.prototype.peek(i)) but I've
        # forgotten what it was. Now looks like a blunder.
        def calc_travel_time_actual(self):
            n = 0
            sum_times = 0 # Initialize sum_times
            for i in range(car_queue_size): # loop through all cars
                c = car_array[i]
                if c and c.route == self and c.odometer > 0: # select only cars on our route that have begun moving
                    v = (c.odometer / (global_clock - c.depart_time)) * speed_limit # speed
                    tt = self.route_length / v # travel time
                    sum_times += tt # sum of travel times for all cars on the route
                    n += 1

            if n == 0:
                self.travel_time = self.route_length / speed_limit # if no cars on this route, use default travel time
            else:
                self.travel_time = sum_times / n # average travel time for all cars on the route


        # A third approach: Use the cumulative statistics on travel times experienced
        # by all cars that have completed the route.
        def calc_travel_time_historical(self):
            if Dashboard.counts[self.label] == 0:
                self.travel_time = self.route_length / speed_limit # if no data, use the default value
            else:
                self.travel_time = Dashboard.times[self.label] / Dashboard.counts[self.label] # average travel time


    # Define the four possible routes as instances of Route().

    Ab = Route()
    Ab.label = "Ab"
    Ab.paint_color = "#cb0130"
    Ab.directions = {"orig": A_link_id, "south": None, "north": b_link_id, "dest": parking_lot} # Use link IDs
    Ab.itinerary = [A_link_id, b_link_id] # Use link IDs
    Ab.calc_route_length()

    aB = Route()
    aB.label = "aB"
    aB.paint_color = "#1010a5"
    aB.directions = {"orig": a_link_id, "south": B_link_id, "north": None, "dest": parking_lot} # Use link IDs
    aB.itinerary = [a_link_id, B_link_id] # Use link IDs
    aB.calc_route_length()

    AB = Route()
    AB.label = "AB"
    AB.paint_color = "#ffc526"
    AB.directions = {"orig": A_link_id, "south": B_link_id, "north": ns_link_id, "dest": parking_lot} # Use link IDs
    AB.itinerary = [A_link_id, ns_link_id, B_link_id] # Use link IDs
    AB.calc_route_length()

    ab = Route()
    ab.label = "ab"
    ab.paint_color = "#4b9b55"
    ab.directions = {"orig": a_link_id, "south": sn_link_id, "north": b_link_id, "dest": parking_lot} # Use link IDs
    ab.itinerary = [a_link_id, sn_link_id, b_link_id] # Use link IDs
    ab.calc_route_length()



    # When a car is about to be launched upon a trip through the road
    # network, we have to choose which route it will follow. In general,
    # the choice is based on the expected travel time, as determined by
    # one of the three methods above. But there are many ways to put the
    # timing information to use.
    # Each of the functions below takes one argument, a list of all
    # available routes. This will be a list of either two or four elements,
    # depending on whether the bridge is closed or open.

    class Chooser: # Group chooser methods in a class for better organization
        # The random chooser just ignores the route timings and chooses
        # one of the available routes uniformly at random.
        def random_choice(self, route_list):
            return random.choice(route_list) # Pythonic random choice

        # The min chooser always takes the route with the shortest expected
        # travel time, no matter how small the advantage might be. If multiple
        # routes have exactly the same time, the choice is random
        def min_choice(self, route_list):
            min_val = float('inf')
            min_routes = []
            for route in route_list: # Pythonic iteration
                if route.travel_time < min_val:
                    min_val = route.travel_time
                    min_routes = [route] # best yet, make sole element of minRoutes
                elif route.travel_time == min_val:
                    min_routes.append(route) # equal times, append to minRoutes list

            if len(min_routes) == 1:
                return min_routes[0] # the one fastest route
            else:
                return random.choice(min_routes) # random choice among all best


        # Rather than the winner-take-all strategy of the min chooser, here we
        # make a random choice with probabilities weighted according to the
        # travel times. Thus a small difference between two routes yields only
        # a slightly greater likelihood.
        def probabilistic_choice(self, route_list):
            val_sum = 0
            for route in route_list: # Pythonic iteration
                route.travel_time = 1 / route.travel_time # inverse of travel time
                val_sum += route.travel_time # sum of the reciprocals

            for route in route_list: # Pythonic iteration
                route.travel_time /= val_sum # normalize so probabilities sum to 1

            r = random.random()
            accum = 0
            for route in route_list: # step through routes until cumulative # Pythonic iteration
                accum += route.travel_time # weighted probability > random r
                if accum > r:
                    return route

    chooser = Chooser() # Instantiate Chooser class


    # The ugly nest of if-else clauses, based on two state variables,
    # routingMode and selectionMethod.
    def choose_route():
        available_routes = [] # Initialize as list
        if bridge_blocked:
            available_routes = [Ab, aB]
        else:
            available_routes = [Ab, aB, AB, ab]

        if routing_mode == "random":
            return chooser.random_choice(available_routes)
        else: # routingMode == "selfish"
            for route in available_routes: # Pythonic iteration
                route.calc_travel_time()

            if selection_method == "minimum":
                return chooser.min_choice(available_routes)
            else: # selectionMethod == "probabilistic"
                return chooser.probabilistic_choice(available_routes)


    # The cars are Javascript objects, with a "abatar" property that holds info
    # about the visual representation in SVG. We put the avatars into the DOM
    # at init time and then leave them there, to avoid the cost of repeated DOM
    # insertions and removals. Cars that aren't currently on the road are still
    # in the DOM but are hidden with display: none.
    # constructor for cars
    class Car:
        def __init__(self):
            self.serial_number = None # invariant assigned at creation, mostly for debugging use
            self.progress = 0 # records distance traveled along a link (reset after leaving link)
            self.past_progress = 0 # at t-1, so we can calculate distance traveled at step t
            self.depart_time = 0 # globalClock reading at orig node
            self.arrive_time = 0 # globalClock reading at dest node
            self.route = None # route chosen for the car at time of launch
            self.odometer = 0 # cumulative distance traveled throughout route (not just link)
            self.avatar = 'car_avatar' # document.createElementNS(xmlns, "circle") # the SVG element - Placeholder for DOM element creation
            # Simulate avatar.setAttribute - Placeholder for DOM manipulation
            # self.avatar.setAttribute("class", "car")
            # self.avatar.setAttribute("cx", 0)
            # self.avatar.setAttribute("cy", 0)
            # self.avatar.setAttribute("r", carRadius)
            # self.avatar.setAttribute("fill", "#000") # will be changed at launch to route color
            # self.avatar.setAttribute("display", "none") # hidden until launched
            # frame.appendChild(self.avatar) # add avatar to the DOM - Placeholder for DOM manipulation
            parking_lot.enqueue(self) # add object to the holding pen


        # Reset a car to default "parked" state, and add it to the
        # parking lot queue. Used when a car reaches the destination node
        # or when the model is reset via UI button.
        def park(self):
            # Simulate avatar.setAttribute - Placeholder for DOM manipulation
            # self.avatar.setAttribute("display", "none")
            # self.avatar.setAttribute("fill", "#000")
            # self.avatar.setAttribute("cx", 0)
            # self.avatar.setAttribute("cy", 0)
            self.route = None
            self.progress = 0
            self.past_progress = 0
            self.odometer = 0
            parking_lot.enqueue(self)


    # Here's where we make all the cars. Note that new Car() enqueues them in
    # parkingLot.
    def make_cars(n):
        for i in range(n): # Pythonic loop
            c = Car()
            c.serial_number = i
            car_array[i] = c


    # runs on load
    def init():
        make_cars(car_queue_size)
        global global_clock # Declare global if you intend to modify it. Not needed if only reading. But it's being modified in step, so declared here for clarity.
        global_clock = 0
        sync_controls()
        a_link.update_speed()
        A_link.update_speed()
        B_link.update_speed()
        b_link.update_speed()
        ns_link.update_speed()
        sn_link.update_speed()
        Dashboard.colorize()
        setup_for_touch()


    # Make sure the on-screen input elements correctly reflect the values
    # of corresponding js variables. (This is needed mainly for Firefox,
    # which does not reset inputs on page reload.)
    def sync_controls():
        # Placeholder for DOM element property access and manipulation
        # congestionSlider.value = congestionCoef;
        # launchRateSlider.value = launchRate;
        # routingModeMenu.value = routingMode;
        # launchTimingMenu.value = launchTiming;
        # speedMenu.value = speedMode;
        # selectionMethodMenu.value = selectionMethod;
        # maxCarsInput.value = "";

        geeky_controls = [ 'geeky_control_1', 'geeky_control_2'] # document.querySelectorAll(".geeky") # Placeholder for DOM querySelectorAll
        for geeky_control in geeky_controls: # Pythonic loop
            # geekyControls[i].style.display = "none"; # Placeholder for DOM style manipulation
            pass # Simulate style.display = "none"
        # geekToggle.textContent = "More controls"; # Placeholder for DOM textContent manipulation
        global geek_mode # Declare global if you intend to modify it
        geek_mode = False


    # Dashboard for recording and displaying stats. The "counts" and "times"
    # dictionaries keep track of how many cars have traversed each route and
    # how long they took to do it. Each of these values is linked to a cell
    # in an HTML table.

    class DashboardClass: # Class name uses PascalCase
        def __init__(self):
            self.departure_count = 0
            self.arrival_count = 0
            self.counts = {
                "Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0
            }
            self.times = {
                "Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0
            }
            self.count_readouts = { # Placeholder for DOM elements
                "Ab": "Ab_count_element", # document.getElementById("Ab-count"), # links to HTML table cells
                "aB": "aB_count_element", # document.getElementById("aB-count"),
                "AB": "AB_count_element", # document.getElementById("AB-count"),
                "ab": "ab_count_element", # document.getElementById("ab-count"),
                "total": "total_count_element" # document.getElementById("total-count")
            }

            self.time_readouts = { # Placeholder for DOM elements
                "Ab": "Ab_time_element", # document.getElementById("Ab-time"),
                "aB": "aB_time_element", # document.getElementById("aB-time"),
                "AB": "AB_time_element", # document.getElementById("AB-time"),
                "ab": "ab_time_element", # document.getElementById("ab-time"),
                "total": "total_time_element" # document.getElementById("total-time")
            }

        def colorize(self):
            # Placeholder for DOM element style manipulation
            # AbRow = document.getElementById("Ab-row"); # make cell backgrounds match car colors
            # AbRow.style.backgroundColor = Ab.paintColor;
            # var aBRow = document.getElementById("aB-row");
            # aBRow.style.backgroundColor = aB.paintColor;
            # var ABRow = document.getElementById("AB-row");
            # ABRow.style.backgroundColor = AB.paintColor;
            # var abRow = document.getElementById("ab-row");
            # abRow.style.backgroundColor = ab.paintColor;
            # var totalRow = document.getElementById("total-row");
            # totalRow.style.backgroundColor = "#000";
            pass # Simulate colorization


        def record_departure(self): # called by launchCar
            self.departure_count += 1

        def record_arrival(self, car): # called by dest.dispatch
            elapsed = (global_clock - car.depart_time) / speed_limit
            route_code = car.route.label
            self.counts[route_code] += 1
            self.counts["total"] += 1
            self.times[route_code] += elapsed # Note: we're storing total time for all cars; need to divide by n
            self.times["total"] += elapsed
            self.update_readouts()


        # For the time readout, we divide total elapsed time by number of
        # cars to get time per car; we then also divide by the duration of the
        # quickest conceivable trip from Origin to Destination. Thus all times
        # are reported in units of this fastest trip.
        def update_readouts(self):
            for ct in self.count_readouts: # Pythonic loop
                # self.countReadouts[ct].textContent = self.counts[ct]; # Placeholder for DOM textContent manipulation
                pass # Simulate textContent update
            for tm in self.time_readouts: # Pythonic loop
                if self.counts[tm] == 0:
                    # self.timeReadouts[tm].textContent = "--"; # Placeholder for DOM textContent manipulation
                    pass # Simulate textContent update
                else:
                    # self.timeReadouts[tm].textContent = ((self.times[tm] / self.counts[tm]) / quickestTrip).toFixed(3); # Placeholder for DOM textContent manipulation
                    pass # Simulate textContent update


        def reset(self): # Reset button blanks out the stats display.
            self.departure_count = 0
            self.arrival_count = 0
            for ct in self.counts: # Pythonic loop
                self.counts[ct] = 0
            for tm in self.times: # Pythonic loop
                self.times[tm] = 0
            self.update_readouts()

    Dashboard = DashboardClass() # Instantiate DashboardClass


    # Event handlers and other routines connected with controls and the user interface.

    # The Go button starts the animation, but the Stop button doesn't stop it.
    # Instead we just set a state variable, change the button text to "Wait",
    # and let any cars still on the road find their way to the destination.
    # The step function -- the procedure run on every time step -- will eventually
    # stop the periodic updates.
    def go_stop_button(): # Pass event 'e' if needed for actual event handling simulation
        global model_state, animation_timer # Declare globals if you intend to modify them

        if model_state == "stopped":
            model_state = "running"
            # goButton.innerHTML = "Stop"; # Placeholder for DOM innerHTML manipulation
            animate()
        elif model_state == "running":
            model_state = "stopping"
            # goButton.innerHTML = "Wait"; # Placeholder for DOM innerHTML manipulation
            # goButton.disabled = True; # Placeholder for DOM disabled property manipulation


    # This is a version of goStopButton that brings the model to an immediate halt,
    # leaving the cars in place on the road. It's useful if you want to take a screen
    # shot of the model in action.
    # def go_stop_button(e):
    # if (modelState === "stopped") {
    # modelState = "running";
    # goButton.innerHTML = "Stop";
    # animate();
    # }
    # else if (modelState === "running") {
    # window.clearInterval(animationTimer);
    # modelState = "stopped";
    # goButton.innerHTML = "Go";
    # goButton.removeAttribute("disabled");
    # }
    # Handler for the Reset button. If the model is running, we need to
    # stop the animation. Then we clear all cars from links and nodes,
    # clear the dashboard, and reset a few globals.
    def reset_model(): # Pass event 'e' if needed for actual event handling simulation
        global model_state, animation_timer, global_clock, next_departure # Declare globals if you intend to modify them
        links_and_nodes = [A_link, a_link, B_link, b_link, ns_link, sn_link, orig, dest, north, south]
        if model_state == "running":
            model_state = "stopped"
            # goButton.innerHTML = "Go"; # Placeholder for DOM innerHTML manipulation
            if animation_timer: # Check if timer is active before clearing
                clear_interval(animation_timer) # window.clearInterval(animationTimer);
                animation_timer = None

        for link_node in links_and_nodes: # Pythonic loop
            link_node.evacuate()

        global_clock = 0
        next_departure = 0
        Dashboard.reset()


    # Handler for the numeric input that allows us to run a specified number
    # of cars through the system.
    def set_max_cars(): # Pass event 'e' if needed for actual event handling simulation
        global max_cars # Declare global if you intend to modify it
        # limit_str = maxCarsInput.value # Placeholder for DOM element value access
        limit_str = "100" # Simulated input value for testing purposes
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 0

        if limit == 0:
            max_cars = float('inf')
        else:
            max_cars = limit


    # Handler for clicks on the bridge in the middle of the roadway network.
    # Initial state is blocked; clicks toggle between open and closed. Visual
    # indicators are handled by altering the classList.
    def toggle_bridge(): # No event 'e' needed as it's a toggle
        global bridge_blocked # Declare global if you intend to modify it
        bridge_blocked = not bridge_blocked
        sn_link.open_to_traffic = not sn_link.open_to_traffic
        ns_link.open_to_traffic = not ns_link.open_to_traffic
        # Simulate classList.toggle - Placeholder for DOM classList manipulation
        # snBridge.classList.toggle("closed");
        # nsBridge.classList.toggle("closed");
        # theBarricade.classList.toggle("hidden");


    # Handler for the Vehicle Launch Rate input (which will be rendered as a
    # slider by most modern browsers).
    def get_launch_rate(): # Pass event 'e' if needed for actual event handling simulation
        global launch_rate, next_departure # Declare globals if you intend to modify them
        # launch_rate_str = launchRateSlider.value # Placeholder for DOM element value access
        launch_rate_str = "0.6" # Simulated input value for testing purposes

        try:
            launch_rate = max(float(launch_rate_str), 0.001)
        except ValueError:
            launch_rate = 0.001

        # launchRateOutput.textContent = launchRate.toFixed(2); # Placeholder for DOM textContent manipulation
        next_departure = global_clock + launch_timer(launch_rate / speed_limit)


    # Handler for the Congestion Coefficient slider.
    def get_congestion_coef(): # Pass event 'e' if needed for actual event handling simulation
        global congestion_coef # Declare global if you intend to modify it
        # congestion_coef_str = congestionSlider.value # Placeholder for DOM element value access
        congestion_coef_str = "0.6" # Simulated input value for testing purposes
        try:
            congestion_coef = float(congestion_coef_str)
        except ValueError:
            congestion_coef = 0.55 # default value

        # congestionOutput.textContent = congestionCoef.toFixed(2); # Placeholder for DOM textContent manipulation


    # Handler for Launch Timing select input.
    def get_launch_timing(): # Pass event 'e' if needed for actual event handling simulation
        global launch_timing, launch_timer # Declare globals if you intend to modify them
        timings = {"poisson": poisson, "uniform": uniform, "periodic": periodic}
        # selected_timing = launchTimingMenu.value; # Placeholder for DOM element value access
        selected_timing = "uniform" # Simulated input value for testing purposes
        launch_timing = selected_timing
        launch_timer = timings[selected_timing]


    # Handler for Routing Mode select input.
    def get_routing_mode(): # Pass event 'e' if needed for actual event handling simulation
        global routing_mode # Declare global if you intend to modify it
        # selected_mode = routingModeMenu.value; # Placeholder for DOM element value access
        selected_mode = "random" # Simulated input value for testing purposes
        routing_mode = selected_mode


    # Handler for Speed Measurement select input.
    def get_speed_mode(): # Pass event 'e' if needed for actual event handling simulation
        global speed_mode # Declare global if you intend to modify it
        # selected_mode = speedMenu.value; # Placeholder for DOM element value access
        selected_mode = "actual" # Simulated input value for testing purposes
        speed_mode = selected_mode


    # Handler for Route Selection Method select input.
    def get_selection_method(): # Pass event 'e' if needed for actual event handling simulation
        global selection_method # Declare global if you intend to modify it
        # selected_mode = selectionMethodMenu.value; # Placeholder for DOM element value access
        selected_mode = "weighted-probability" # Simulated input value for testing purposes
        selection_method = selected_mode


    # With two sliders, four drop-down menus, a couple of buttons, and a numeric
    # input control, the UI looks a bit intimidating. To avoid scaring people away
    # on first acquaintance, we can hide all but the most basic controls, and
    # display the rest only on request. This is a handler for clicks on a "More
    # controls"/"Fewer controls" element at the bottom of the control panel.
    def toggle_geek_mode(): # Pass event 'e' if needed for actual event handling simulation
        global geek_mode # Declare global if you intend to modify it
        geeky_controls = ['geeky_control_1', 'geeky_control_2'] # document.querySelectorAll(".geeky"); # Placeholder for DOM querySelectorAll
        if geek_mode:
            for geeky_control in geeky_controls: # Pythonic loop
                # geekyControls[i].style.display = "none"; # Placeholder for DOM style manipulation
                pass # Simulate style.display="none"
            # geekToggle.textContent = "More controls"; # Placeholder for DOM textContent manipulation
        else:
            for geeky_control in geeky_controls: # Pythonic loop
                # geekyControls[i].style.display="block"; # Placeholder for DOM style manipulation
                pass # Simulate style.display="block"
            # geekToggle.textContent = "Fewer controls"; # Placeholder for DOM textContent manipulation

        geek_mode = not geek_mode

    # Tooltips, or "hover hints", explain what all the geeky controls are supposed
    # to control. But the hints themselves are annoying after you've seen them the
    # first few times, so we provide a ways to turn them off. This is the click
    # handler for the "Show/Hide hover hints" element at the bottom of the control panel.
    # The hint implementation is a CSS-only solution by Kushagra Gour (see hint.css).
    # The easy way to turn it off and on is by disabling the whole stylesheet.
    def toggle_hints(): # Pass event 'e' if needed for actual event handling simulation
        global hint_mode # Declare global if you intend to modify it
        if hint_mode:
            # hintStylesheet.disabled = True; # Placeholder for DOM stylesheet disabled property manipulation
            pass # Simulate stylesheet.disabled = True
            # hintToggle.textContent = "Show hover hints"; # Placeholder for DOM textContent manipulation
        else:
            # hintStylesheet.disabled = False; # Placeholder for DOM stylesheet disabled property manipulation
            pass # Simulate stylesheet.disabled = False
            # hintToggle.textContent = "Hide hover hints"; # Placeholder for DOM textContent manipulation

        hint_mode = not hint_mode


    # Set up for Touch devices. Kill the hints and the geek mode. Uses class
    # added to the html tag by modernizr.
    def setup_for_touch():
        # Simulate Modernizr.touch - Assuming it's always False for non-browser env.
        is_touch_device = False # Modernizr.touch
        if is_touch_device:
            global geek_mode, hint_mode # Declare globals if you intend to modify them
            if geek_mode:
                toggle_geek_mode()

            if hint_mode:
                toggle_hints()

            # geekToggle.style.display = "none"; # Placeholder for DOM style manipulation
            # hintToggle.style.display = "none"; # Placeholder for DOM style manipulation


    # Prints the contents of the Dashboard panel to the console at the end of the
    # run. Disabled by default; to activate, uncomment the line toward the end of
    # the step function, below.
    def save_stats():
        routes = ["Ab", "aB", "AB", "ab"]
        print("launch_rate:", launch_rate, "congestion_coef:", congestion_coef, "bridge_blocked:", bridge_blocked)
        for route in routes: # Pythonic loop
            # Placeholder for DOM textContent access
            count_text = "10" # Dashboard.countReadouts[route].textContent # Simulated value
            time_text = "0.5" # Dashboard.timeReadouts[route].textContent # Simulated value
            print(route, count_text, time_text)

        # Placeholder for DOM textContent access
        total_count_text = "40" # Dashboard.countReadouts["total"].textContent # Simulated value
        total_time_text = "2.0" # Dashboard.timeReadouts["total"].textContent # Simulated value
        print("total", total_count_text, total_time_text)


    # Just for producing graphs of occupancy levels; in default configuration,
    # the only call to this function is commented out. When activated, carCensus
    # logs the number of cars on each route at each time step. The output is a sequence
    # of five numbers: time, Ab, aB, AB, ab.
    def car_census(sample_interval):
        route_counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0}
        census = [global_clock, 0, 0, 0, 0]
        if Dashboard.departure_count > 10000 and global_clock % sample_interval == 0:
            for c in car_array: # Pythonic loop
                if c and c.route:
                    route_counts[c.route.label] += 1

            print(global_clock / speed_limit, route_counts["Ab"], route_counts["aB"], route_counts["AB"], route_counts["ab"])


    # Here we're at the starting line -- the procedure that prepares a car to
    # run the course and hands it off to the Origin node. But it's more complicated
    # than it should be. Not every call to launchCar actually launches a car.
    # Abstractly, here's what happens. At intervals determined by our timer
    # function, a departure time is put on the schedule (by setting the global
    # variable nextDeparture). LaunchCar runs on each clock tick, and checks to
    # see if globalClock >= nextDeparture. However, the car can actually be launched
    # at that moment only if there is room for it in the orig node buffer. This
    # has nontrivial consequences when cars are being launched at high frequency.
    def launch_car():
        global next_departure # Declare global if you intend to modify it
        if orig.has_room() and global_clock >= next_departure and model_state == "running" and parking_lot.len > 0:
            next_car = parking_lot.dequeue()
            next_car.depart_time = global_clock
            next_car.route = choose_route()
            # Simulate avatar.setAttribute - Placeholder for DOM manipulation
            # nextCar.avatar.setAttribute("fill", nextCar.route.paintColor);
            # nextCar.avatar.setAttribute("cx", orig.x);
            # nextCar.avatar.setAttribute("cy", orig.y);
            # nextCar.avatar.setAttribute("display", "block");
            orig.accept(next_car)
            Dashboard.record_departure()
            next_departure = global_clock + launch_timer(launch_rate / speed_limit)


    # The step function is the main driver of the simulation. The idea is
    # to poll all the nodes and links, moving cars along their route. But
    # in what sequence should we examine the nodes and links. It makes sense
    # to work backwards through the network, clearing space in later nodes
    # and links so that cars behind them can move up.
    # There's another, subtler issue of sequencing. Every node except orig
    # has two links feeding into it. If we always attend to those links in the
    # same order, the later one might never get a chance to advance, if the
    # earlier one keeps the node always occupied. I thought I could avoid this
    # problem by simply alternating the sequence, but a deadlock is still
    # possible in heavy traffic. Randomizing the sequence seems to work well.
    def step():
        global num_of_steps, model_state, animation_timer, global_clock # Declare globals if you intend to modify them
        num_of_steps += 1
        if coin_flip():
            dest.dispatch()
            b_link.drive()
            dest.dispatch()
            B_link.drive()
        else:
            dest.dispatch()
            B_link.drive()
            dest.dispatch()
            b_link.drive()

        if coin_flip():
            north.dispatch()
            A_link.drive()
            north.dispatch()
            sn_link.drive()
        else:
            north.dispatch()
            sn_link.drive()
            north.dispatch()
            A_link.drive()

        if coin_flip():
            south.dispatch()
            ns_link.drive()
            south.dispatch()
            a_link.drive()
        else:
            south.dispatch()
            a_link.drive()
            south.dispatch()
            ns_link.drive()

        orig.dispatch()
        launch_car()
        orig.dispatch()
        launch_car()
        # carCensus(9); # uncomment to log route occupancy numbers on every time step
        global_clock += speed_limit

        if model_state == "stopping" and parking_lot.len == car_queue_size: # all cars back in the barn, shut down
            if animation_timer:
                clear_interval(animation_timer) # window.clearInterval(animationTimer);
                animation_timer = None
            model_state = "stopped"
            # goButton.innerHTML = "Go"; # Placeholder for DOM innerHTML manipulation
            # goButton.removeAttribute("disabled"); # Placeholder for DOM removeAttribute manipulation
            print(num_of_steps)
            # saveStats(); # uncomment to output a summary of the run to the JS console

        if model_state == "running" and Dashboard.departure_count >= max_cars: # enough cars, stop launching
            model_state = "stopping"
            # goButton.innerHTML = "Wait"; # Placeholder for DOM innerHTML manipulation
            # goButton.setAttribute("disabled", True); # Placeholder for DOM setAttribute manipulation
            # print(numOfSteps);


    def animate(): # called by Go button event handler
        global animation_timer # Declare global if you intend to modify it

        def set_interval(function, milliseconds):
            def inner_function():
                function()
                return True # Simulate interval return

            return inner_function # Return the inner function itself

        def clear_interval(timer):
            pass # No actual clearing needed in this simulation context

        animation_timer = set_interval(step, 15) # window.setInterval(step, 15); # 15 milliseconds = roughly 60 frames per second
        # Simulate initial call to step to start interval if needed, or rely on external loop to call animate/step.
        # step() # Uncomment if you need to trigger the first step immediately.

    class Queue: # Assuming Queue class is defined in queue.py, or needs to be implemented.
        def __init__(self, capacity):
            self.capacity = capacity
            self.items = []
            self.len = 0 # Keep track of length

        def enqueue(self, item):
            if self.len < self.capacity:
                self.items.append(item)
                self.len += 1
            else:
                print("Queue overflow!")

        def dequeue(self):
            if self.len > 0:
                item = self.items.pop(0)
                self.len -= 1
                return item
            else:
                return None # Or raise an exception for empty queue

        def peek(self, index):
            if 0 <= index < self.len:
                return self.items[index]
            else:
                return None # Or raise an exception for index out of range

        def last(self): # Mimic last() method
            if self.len > 0:
                return self.items[-1]
            return None


    launch_timer = poisson # Initialize launch_timer before init is called.
    init()

    # Simulate event listeners - In Python, event handling is different, especially in non-browser environments.
    # These are just function calls for demonstration. In a real Python GUI or simulation, you'd use
    # appropriate event handling mechanisms.
    # snBridge.addEventListener("click", toggleBridge, false);
    # Simulate event listener for sn_bridge
    toggle_bridge() # Simulate click event

    # nsBridge.addEventListener("click", toggleBridge, false);
    # Simulate event listener for ns_bridge
    toggle_bridge() # Simulate click event

    # theBarricade.addEventListener("click", toggleBridge, false);
    # Simulate event listener for the_barricade
    toggle_bridge() # Simulate click event

    # goButton.addEventListener("click", goStopButton, false);
    # Simulate event listener for go_button
    go_stop_button() # Simulate click event

    # resetButton.addEventListener("click", resetModel, false);
    # Simulate event listener for reset_button
    reset_model() # Simulate click event

    # maxCarsInput.addEventListener("input", setMaxCars, false);
    # Simulate event listener for max_cars_input (input event)
    set_max_cars() # Simulate input event

    # launchRateSlider.addEventListener("input", getLaunchRate, false);
    # Simulate event listener for launch_rate_slider (input event)
    get_launch_rate() # Simulate input event

    # launchRateOutput. Placeholder - Output update already handled in get_launch_rate

    # congestionSlider.addEventListener("input", getCongestionCoef, false);
    # Simulate event listener for congestion_slider (input event)
    get_congestion_coef() # Simulate input event

    # congestionOutput. Placeholder - Output update already handled in get_congestion_coef

    # launchTimingMenu.addEventListener("change", getLaunchTiming, false);
    # Simulate event listener for launch_timing_menu (change event)
    get_launch_timing() # Simulate change event

    # routingModeMenu.addEventListener("change", getRoutingMode, false);
    # Simulate event listener for routing_mode_menu (change event)
    get_routing_mode() # Simulate change event

    # speedMenu.addEventListener("change", getSpeedMode, false);
    # Simulate event listener for speed_menu (change event)
    get_speed_mode() # Simulate change event

    # selectionMethodMenu.addEventListener("change", getSelectionMethod, false);
    # Simulate event listener for selection_method_menu (change event)
    get_selection_method() # Simulate change event

    # geekToggle.addEventListener("click", toggleGeekMode, false);
    # Simulate event listener for geek_toggle (click event)
    toggle_geek_mode() # Simulate click event

    # hintToggle.addEventListener("click", toggleHints, false);
    # Simulate event listener for hint_toggle (click event)
    toggle_hints() # Simulate click event

    # hintStylesheet. Placeholder - Stylesheet manipulation already handled in toggle_hints

    animate() # Start the animation loop

if __name__ == "__main__":
    rewrite_code_to_python()


