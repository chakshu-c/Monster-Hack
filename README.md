# 👻 Monster Hack: AI Monster Detector

Our entry for **Data CoLab's Mini Monster Hack** (Wed 28 October, Queens Tower Rooms, South Kensington Campus): a 5-hour, beginner-friendly AI and data challenge.

A synthetic learning-analytics dataset (LMS and video activity) has been invaded by monsters. Our job is to find them, build a detector, test it on unseen data, and predict which students might be starting to transform next.

## The challenge

| Stage | Goal |
|---|---|
| 🔍 **Hunt** | Find unusual patterns and monster behaviour hidden in the training data |
| 🧠 **Train** | Build an AI Monster Detector |
| 🧪 **Test** | Check whether the detector finds monsters in unseen data |
| 🔮 **Predict** | Predict which students may be starting to transform next |
| 🎤 **Show** | Present our approach, outputs and working model |

## The monsters

**Data anomalies**

| Monster | How to spot it |
|---|---|
| 👻 **The Phantom** | Student has a duplicate activity row (LMS or video) |
| 🧟‍♂️ **The Undead Student** | Activity recorded after the student's deregistration date |
| 👯 **The Doppelgänger** | Two students with suspiciously identical activity (both P_IDs are reported, one per row) |
| 🦎 **The Shape-Shifter** | Student appears to switch programme during the year |

**Behavioural monsters**

| Monster | How to spot it |
|---|---|
| 🌫️ **The Ghost** | Active in ≥3 of the first 4 weeks of Autumn term, then later average weekly activity is <10% of their early weekly average |
| 🧟 **The Zombie** | Continuous activity (no gap longer than 15 minutes) for more than 3 hours |
| 🧛 **The Vampire** | More days with night activity (midnight to 5am) than day activity (5am to midnight), and more than 21 night-active days |
| 🐺 **The Werewolf** | Spikes in activity throughout the Autumn and Spring terms |
| 🕷️ **The Web Crawler** | More than 200 LMS items or videos within a 12-hour block |

## Our approach

1. **Hunt:** wrote one rule-based detector per monster, straight from the Monster Guide, and ran them on the training data.
2. **Train:** built per-student features (weekly activity, night/day split, longest session, 12-hour peaks, spikes, etc.) and trained a classifier on the labels from the hunt.
3. **Test:** ran the rules and the model on the unseen data and compared the results.
4. **Predict:** ranked students who aren't monsters yet by how close they are to each threshold, plus their model probability.

_(Update this with what you actually did on the day.)_

## Repo structure

```
├── data/          # dataset goes here (not committed)
├── notebooks/     # exploration + modelling notebooks
├── src/           # loading, detectors, features
├── outputs/       # submission CSVs (P_ID, monster)
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone https://github.com/chak720/Monster-Hack.git
cd Monster-Hack
python3.11 -m venv myvenv
source myvenv/bin/activate        # Windows: myvenv\Scripts\activate
pip install -r requirements.txt
```

Put the dataset files in `data/`, then open the notebooks with `jupyter lab`.

## Results

| Monster | Found in training | Found in test |
|---|---|---|
| Phantom | – | – |
| Ghost | – | – |
| Zombie | – | – |
| Vampire | – | – |
| Undead Student | – | – |
| Doppelgänger | – | – |
| Werewolf | – | – |
| Web Crawler | – | – |
| Shape-Shifter | – | – |

## Team

- Chakshu Chopra
- _teammate_
- _teammate_
- _teammate_

## Acknowledgements

The dataset is synthetic and was provided by Data CoLab for the Mini Monster Hack. It contains no real student data.
