import math


class Tracker:
    def __init__(self, tracking_distance):
        self.tracking_distance = tracking_distance
        self.object_count = 0
        self.previous_frame_data = {}
        self.tracked_objects = {}
        self.for_processing = {}

    def update(self, detected_objects, frequency, scaling_coefficient):
        found_objects = []

        for detected_object in detected_objects:
            x, y, r = detected_object
            cx = (x + x + r) // 2
            cy = (y + y + r) // 2

            same_object = False

            for object_id, object_data in self.previous_frame_data.items():
                dist = math.hypot(cx - object_data[0], cy - object_data[1])
                if dist < self.tracking_distance:
                    if r - 3 >= self.tracked_objects[object_id][1]:
                        break
                    found_objects.append([x, y, r, object_id])
                    self.previous_frame_data[object_id] = (cx, cy)
                    frames, radius, distance, speed = self.tracked_objects[object_id]
                    frames += 1
                    self.tracked_objects[object_id] = (
                        frames,
                        radius,
                        distance + dist,
                        scaling_coefficient * distance / (frames / frequency)
                    )
                    self.for_processing[object_id] = (
                        frames,
                        radius,
                        distance + dist,
                        distance / (frames / frequency)
                    )
                    same_object = True
                    print(self.tracked_objects)
                    break

            if not same_object:
                self.previous_frame_data[self.object_count] = (cx, cy)
                self.tracked_objects[self.object_count] = (0, r, 0, 0)
                found_objects.append([x, y, r, self.object_count])
                self.object_count += 1

        new_previous_frame_data = {}
        new_tracked_objects = {}
        for found_object in found_objects:
            _, _, _, object_id = found_object
            new_previous_frame_data[object_id] = self.previous_frame_data[object_id]
            new_tracked_objects[object_id] = self.tracked_objects[object_id]

        self.previous_frame_data = new_previous_frame_data.copy()
        self.tracked_objects = new_tracked_objects.copy()

        return found_objects
