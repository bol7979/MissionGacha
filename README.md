MissionGacha — README
==


🎯 MissionGacha(미션가챠)란?
--
MissionGacha(미션가챠)는 행동주의 심리학 이론인 [조작적 조건화](https://ko.wikipedia.org/wiki/%EC%A1%B0%EC%9E%91%EC%A0%81_%EC%A1%B0%EA%B1%B4%ED%99%94)에 영감을 받아 **자기통제/습관 형성**을 도울 목적으로 제작되었습니다.<br/>
사용자가 스스로 정한 미션을 달성하면 "가챠(뽑기)"를 돌려 무작위의 보상을 얻습니다.<br/>
(보상이 주효하려면 **통제**가 꼭 필요합니다. 유튜브를 원할 때마다 보는 사람이 '유튜브 5분 시청'을 뽑는다면 그건 보상이 아니니까요.)


✨ 어떤 기능이 있나요?
---
- 바람직한 행동에 대한 보상을 **변동비율**로 제공하여 행동의 **긍정적 강화**를 유발합니다.
- 미션의 난이도에 따라 **보상 등급**을 **제한**할 수 있습니다.
- 보상 종류의 **추가 및 수정**이 편리합니다.
- 밋밋한 가챠가 되지 않도록 **연출**을 추가하였습니다.
- 보상의 **기록과 통계**를 확인할 수 있습니다.


🚀 설치 및 실행
---
1. 폴더에 `gacha.py` 저장 및 실행
2. 처음 실행 시 `config.json`, `rewards.json`, `history.json`를 폴더에 생성합니다.
3. 아래의 **보상 목록 작성법**을 참조하여 `rewards.json`을 작성합니다. (파일에는 예시가 작성되어 있습니다.)


⚙️ 설정(`config.json`)
---
```json
{
  "use_difficulty_lock": true,
  "grade_unlock_map": {
      "EASY":   ["BASIC"],
      "MEDIUM": ["BASIC","RARE"],
      "HARD":   ["BASIC","RARE","EPIC"]
  },
  "spinner": {
      "cycles": 3,
      "duration_ms": 0,
      "fps": 30,
      "ease_out": true,
      "overshoot": true,
      "window": 5,
      "palette": "neon",
      "final_blink": 4,
      "confetti": true,
      "beep": false,
      "seed": null
  }
}
```
- `use_difficulty_lock`:
    - `true`: 미션 난이도에 허용된 등급의 보상만 추첨
    - `false`: 무조건 모든 등급의 보상에서 추천
- `grade_unlock_map`: 난이도별 허용 등급
- `cycles` 또는 `duration_ms`로 가챠 소요 시간 제어.


🎁 보상 목록(`rewards.json`) 작성법
---
```json
[
  {
    "id": "walk10m",
    "name": "동네 산책 10분",
    "grade": "BASIC",
    "weight": 1.0,
    "enabled": true
  }
]
```
- `id`: 보상을 구분하기 위한 id입니다. 미입력 시 자동으로 **UUID**가 할당됩니다. 크게 신경 쓰지 않아도 됩니다.
- `grade`: 보상의 등급입니다. 기본은 **`BASIC` / `RARE` / `EPIC`** 으로 구성됩니다.
- `weight`: 확률의 가중치입니다.
- `enabled`: `false`시 비활성화


🔍보상 목록(`rewards.json`) 작성 예시
---
```json
[
  { "name": "Short Video (5m)", "grade": "BASIC", "weight": 3, "enabled": true },
  { "name": "Game (30m)",       "grade": "BASIC", "weight": 2, "enabled": true },
  { "name": "Music Break",      "grade": "BASIC", "weight": 3, "enabled": true },
  { "name": "Cafe Drink",       "grade": "RARE",  "weight": 1, "enabled": true },
  { "name": "Movie Episode",    "grade": "RARE",  "weight": 1, "enabled": true },
  { "name": "Delivery Meal",    "grade": "EPIC",  "weight": 1, "enabled": true }
]
```


🎮 사용 방법 (당첨 기록은 `history.json`을 참조)
---
```python
python gacha.py EASY
python gacha.py MEDIUM
python gacha.py HARD
```
- `python gacha.py 난이도`
```python
python gacha.py --validate
```
- `rewards.json`에 중복된 `id`, 잘못된 `grade`, 음수의 `weight`가 있는지 확인합니다.
```python
python gacha.py --stats
python gacha.py --stats=30
```
- `python gacha.py --stats`: 난이도와 등급별 분포, 최다 보상 5순위까지를 출력합니다.
- `python gacha.py --stats=30`: 최근 30개의 결과에 대해서만 통계를 출력합니다.


🧩 조언
---
- 복잡해 보여서 꺼려진다면 난이도에 따른 보상 등급 제한 기능(`use_difficulty_lock`)을 `false`로 설정하여 시작해 보세요.
- 스스로 쉬운 미션만 반복하게 된다면:
  - `weight`를 조절하여 `BASIC`의 확률 가중치를 줄여보세요.
  - `EPIC` 보상의 희소성을 더 높게 설정해 보세요.
- 일상적으로 하는 행동을 보상으로 설정한다면 보상의 효과가 줄어들어요.
