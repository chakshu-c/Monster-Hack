import pandas as pd

lms_df = pd.read_csv("la_mmh_training_lms_item_activity_by_session_fact.csv")
video_df = pd.read_csv("la_mmh_training_video_activity_by_view_fact.csv")

combined = pd.concat([lms_df, video_df], ignore_index=True)
combined = combined.rename(columns={"TIMESTAMP": "timestamp"})
combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
combined = combined.sort_values(["P_ID", "timestamp"]).reset_index(drop=True)

# Treat delivered video minutes as continuous viewing from its timestamp.
# LMS interactions have no viewing duration, so their end equals their start.
combined["activity_end"] = combined["timestamp"] + pd.to_timedelta(
    combined["TOTAL_MINUTES_DELIVERED"].fillna(0), unit="m"
)

max_gap = pd.Timedelta(minutes=15)
min_duration = pd.Timedelta(hours=3)
flagged_sessions = []

for person_id, activity in combined.groupby("P_ID", sort=False):
    session_start = None
    session_end = None

    for start, end in activity[["timestamp", "activity_end"]].itertuples(
        index=False, name=None
    ):
        if session_start is None:
            session_start, session_end = start, end
        elif start - session_end < max_gap:
            # Keep the latest end in case videos overlap other interactions.
            session_end = max(session_end, end)
        else:
            if session_end - session_start > min_duration:
                flagged_sessions.append((person_id, session_start, session_end))
            session_start, session_end = start, end

    # Check the user's final session too.
    if session_end - session_start > min_duration:
        flagged_sessions.append((person_id, session_start, session_end))

flagged_sessions = pd.DataFrame(
    flagged_sessions, columns=["P_ID", "session_start", "session_end"]
)
flagged_sessions["duration_hours"] = [
    (end - start).total_seconds() / 3600
    for _, start, end in flagged_sessions.itertuples(index=False, name=None)
]

print(flagged_sessions)
