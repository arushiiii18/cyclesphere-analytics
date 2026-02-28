def simulate_change(row, change_type):
    """
    Simulate a small lifestyle change and return both
    individual factor scores AND total penalty score.

    Returns
    -------
    dict with keys:
        sleep_score, stress_score, exercise_score,
        total_penalty_score,
        sleep_hours, stress_score_val, exercise_frequency
    """

    sleep = row["sleep_hours"]
    stress = row["stress_score_baseline"]
    exercise = row["exercise_frequency"]

    #Apply simulated change
    if change_type == "sleep":
        sleep = sleep + 1

    elif change_type == "stress":
        stress = max(stress - 1, 0)

    elif change_type == "exercise":
        if exercise is None or str(exercise).startswith("1"):
            exercise = "3–4 days/week"
        elif str(exercise).startswith("3"):
            exercise = "5+ days/week"
        # already at 5+, no change

    #Re-score sleep
    if sleep < 6:
        sleep_score = 2
    elif sleep < 7.5:
        sleep_score = 1
    else:
        sleep_score = 0

    #Re-score stress
    if stress >= 4:
        stress_score = 2
    elif stress == 3:
        stress_score = 1
    else:
        stress_score = 0

    #Re-score exercise
    if exercise is None:
        exercise_score = 0
    else:
        ex_str = str(exercise)
        if ex_str.startswith("1"):
            exercise_score = 2
        elif ex_str.startswith("3"):
            exercise_score = 1
        else:
            exercise_score = 0

    total_score = sleep_score + stress_score + exercise_score

    return {
        "sleep_score": sleep_score,
        "stress_score": stress_score,
        "exercise_score": exercise_score,
        "total_penalty_score": total_score,
        "sleep_hours": sleep,
        "stress_score_val": stress,
        "exercise_frequency": exercise,
    }