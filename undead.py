print("Starting...")
import pandas as pd

folder = r"C:\Users\chaks\Downloads\OneDrive_8_28-10-2026"

print("Loading...")
lms    = pd.read_csv(folder + r"\la_mmh_training_lms_item_activity_by_session_fact.csv", usecols=["P_ID", "DATE"])
video  = pd.read_csv(folder + r"\la_mmh_training_video_activity_by_view_fact.csv",     usecols=["P_ID", "DATE"])
people = pd.read_csv(folder + r"\la_mmh_training_person_dim.csv", na_values=["null"])   # "null" = still registered

activity = pd.concat([lms, video])
activity["DATE"] = pd.to_datetime(activity["DATE"])
people["deregistration_date"] = pd.to_datetime(people["deregistration_date"])

def find_undead(activity, people):
    # 1. Each student's LAST day of activity
    last_active = activity.groupby("P_ID")["DATE"].max().rename("last_activity")

    # 2. Only students who actually deregistered
    left = people.dropna(subset=["deregistration_date"]).set_index("P_ID")

    # 3. Compare: active AFTER they left?
    left = left.join(last_active)
    undead = left[left["last_activity"] > left["deregistration_date"]].copy()
    undead["days_after_leaving"] = (undead["last_activity"] - undead["deregistration_date"]).dt.days
    return undead[["deregistration_date", "last_activity", "days_after_leaving"]].sort_values("days_after_leaving", ascending=False)

undead = find_undead(activity, people)
print("Students who deregistered:", people["deregistration_date"].notna().sum())
print(undead)
print("Number of undead students:", len(undead))
undead.reset_index()[["P_ID"]].assign(Monster="Undead Student").to_csv(folder + r"\undead.csv", index=False)
print("Saved undead.csv")