# FC-Bot

FC-Bot은 EA FC 시리즈 클럽모드(11 vs 11)를 플레이하는 디스코드 커뮤니티, 서버를 관리하고 자동화, 여러 기능을 수행하는 Python 기반 봇입니다.

다양한 기능을 제공하여 커뮤니티 활동을 보다 편리하게 도와줍니다.

## 주요 기능

- 서버 관리 명령어 커스터마이즈
  - 반복멘션
  - 서버 로그 기록
- 팀 게임 관리
  - 출석체크
- 친선 매칭 기능
  - 드래프트 기능
  - 드래프트 대기 리스트 및 관리 기능
  - 주사위 기능
  - 포지션 뽑기 기능
- 팀 관리 자동화 (구현중)
- 경기 일정 관리 및 알림 (구현중)
- 선수 통계 추적 (구현중)
- 실시간 경기 업데이트 및 알림 (구현중)

## 설치 방법

1. **Repository Clone:**

```bash
git clone https://github.com/real2u2l8/FC-Bot.git
cd FC-Bot
```

2. **필요한 패키지 설치:**

```bash
pip install -r requirements.txt
```

3. **봇 설정:**

- 디스코드 봇 토큰 및 필요한 설정 추가.
```bash
mv config.json.bak config.json
```

4. **봇 실행:**

```bash
python FC-Bot.py
```

## 사용법

- 봇을 디스코드 서버에 추가.
- 미리 정의된 명령어 사용.
- cogs와 utils 디렉토리의 스크립트를 수정하여 봇 커스터마이즈.

## 라이선스

이 프로젝트는 GNU General Public License v3.0 라이선스 하에 배포됩니다.

자세한 내용은 LICENSE 파일을 참조하세요.

## 기여

리포지토리를 포크하고, 이슈를 제출하고, 풀 리퀘스트를 보내주세요. 기여는 언제나 환영입니다!

## 문의

문의 사항이나 지원이 필요하면 GitHub Issues를 통해 SEOSLE에게 연락하세요.

자세한 정보는 GitHub 리포지토리에서 확인하세요.
