#
# Takes simulation results and generates a nice readable description summarizing
# the stop

from constants import ViolationType, LocationType, ROADSIDE_STOP_ID, NULL_TIME

def generate_stop_description(results, locations, stop_num):
    stop = results.stop_driving.iloc[stop_num]
    prev_start = results.start_driving.loc[stop["prev_start"]]
    next_start = results.start_driving.loc[stop["next_start"]]
    trip_start = results.start_driving.loc[stop["trip_start"]]
    stop_loc_id = stop["locationID"]
    stop_loc = (
        locations.loc[stop_loc_id]
        if stop_loc_id != ROADSIDE_STOP_ID
        else None
    )
    stop_time = stop.name
    prev_stop_time = trip_start["prev_stop"]
    orig_loc_id = (
        results.stop_driving.loc[prev_stop_time]["locationID"]
        if prev_stop_time != NULL_TIME
        else None
    )
    orig_loc = (
        locations.loc[orig_loc_id]
        if orig_loc_id is not None
        else None
    )
    dest_loc_id = prev_start["destinationID"]
    dest_loc = locations.loc[dest_loc_id]
    next_dest_loc_id = next_start["destinationID"]
    next_dest_loc = (
        locations.loc[next_dest_loc_id]
    )

    def make_trip_text():
        orig = orig_loc["NAME"] if orig_loc is not None else "NULL"
        dest = dest_loc["NAME"]
        verb = "delivering" if stop["is_hauling"] else "picking up"
        return f"Trucker is driving from {orig} to {dest}, {verb} a load"

    def make_hours_driven_text():
        driving_hrs = stop.name - prev_start.name
        return f"Trucker drove for {driving_hrs:.2f} hours since last stop"

    def make_location_text():
        loc_text = "Trucker stopped "
        is_parking_viol = (
            stop["viol"] == ViolationType.PARKING
            or stop["viol"] == ViolationType.DOUBLE
        )
        if stop_loc is None:
            if is_parking_viol:
                loc_text += "in an unsafe location. *** VIOLATION ***"
            else:
                loc_text += "at the shipper/receiver."
        else:
            if stop_loc["type"] == LocationType.CITY:
                loc_text += f"in city {stop_loc['NAME']}, {stop_loc['ST']}."
            elif stop_loc["type"] == LocationType.REST_AREA:
                loc_text += f"at rest area: {stop_loc['name']}."
            elif stop_loc["type"] == LocationType.TRUCK_STOP:
                loc_text += f"at truck stop: {stop_loc['name']}."
        return loc_text

    def make_rest_text():
        rest_hrs = next_start.name - stop.name
        rest_type = stop["restType"]
        return f"Trucker stopped for {rest_type}, {rest_hrs:.2f} hours long"

    def make_hours_remaining_sentences():
        is_hours_viol = (
            stop["viol"] == ViolationType.HOURS
            or stop["viol"] == ViolationType.DOUBLE
        )
        limits = {
            "daily driving hours": stop["drivingHoursUntilLongRest"],
            "hours until 30min rest": stop["drivingHoursUntilShortRest"],
            "7-day driving hours": stop["hoursRemaining7Day"],
            "8-day driving hours": stop["hoursRemaining8Day"],
            "daily on-duty hours": stop["workingHoursUntilLongRest"],
        }
        return [
            (
                f"Remaining {name}: {hours:.2f}. "
                + ("*** VIOLATION ***" if hours < 0 and is_hours_viol else "")
            )
            for name, hours in limits.items()
        ]

    def make_next_step_text():
        is_at_dest = next_start["new_trip"]
        verb = "start a new trip" if is_at_dest else "continue"
        dest = f"{next_dest_loc['NAME']}, {next_dest_loc['ST']}"
        return f"Trucker will {verb} toward {dest}"

    def make_day_text():
        raise Exception("TODO")
        cur_time = f"Stop occurred at {stop_oclock}."

    return [
        make_trip_text(),
        make_location_text(),
        make_hours_driven_text(),
        make_rest_text(),
        make_next_step_text(),
        "\n",
        *make_hours_remaining_sentences(),
        "\n",
        make_day_text()
    ]
