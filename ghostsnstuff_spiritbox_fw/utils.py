import random

def clamp(n, minimum, maximum):
    return max(minimum, min(n, maximum))

def weighted_ghost_choice(activity_level):
    primary_weight = 0
    secondary_weight = 0
    both_weight = 0

    if activity_level <= 3:
        # At levels 1-3, only primary ghost is active
        primary_weight = 10
    elif activity_level == 4:
        # At level 4, the secondary ghost becomes an option
        primary_weight = 8
        secondary_weight = 2
    elif activity_level == 5:
        # At level 5, secondary gains more presence
        primary_weight = 7
        secondary_weight = 3
    elif activity_level == 6:
        # At level 6, we aim for a 60% primary, 40% secondary split
        primary_weight = 6
        secondary_weight = 4
    elif activity_level == 7:
        # At level 7, we aim for a 50/50 split
        primary_weight = 5
        secondary_weight = 5
    elif activity_level == 8:
        # At level 8, we introduce both with 30% primary, 30% secondary, 40% both
        primary_weight = 3
        secondary_weight = 3
        both_weight = 4
    elif activity_level == 9:
        # At level 9, 20% primary, 20% secondary, 60% both
        primary_weight = 2
        secondary_weight = 2
        both_weight = 6
    elif activity_level == 10:
        # At level 10, 5% primary, 5% secondary, 90% both
        primary_weight = 0.5
        secondary_weight = 0.5
        both_weight = 9

    # Create a list of options and corresponding weights
    options = ["primary", "secondary", "both"]
    weights = [primary_weight, secondary_weight, both_weight]

    # Normalize weights to ensure valid distribution
    total_weight = sum(weights)
    if total_weight == 0:
        return "primary"

    # Choose based on the weighted distribution
    return random.choices(options, weights=weights, k=1)[0]