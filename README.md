# unreal-test

언리얼 엔진으로 제작한 카툰 스타일 전투 프로토타입입니다.

## 실행

- 개발 환경: Unreal Engine 5.8.4, Windows, Visual Studio C++ 빌드 도구
- Git LFS 설치 후 저장소를 복제하고 `git lfs pull`을 실행합니다.
- `test.uproject`를 설치된 엔진에 연결하고 프로젝트 파일을 생성합니다. 현재 EngineAssociation은 개발 PC의 로컬 엔진 ID이므로 다른 PC에서는 엔진 버전을 다시 지정해야 합니다.
- `testEditor` Development / Win64를 빌드하고 에디터에서 `/Game/ComicCombat/Maps/ComicArena`를 엽니다.
- `Plugins/UnrealMCP` 소스를 포함하며 플러그인 바이너리는 로컬에서 빌드합니다.

## 조작

| 입력 | 동작 |
|---|---|
| WASD | 이동 |
| Shift 누르기 | 달리기 |
| Space | 점프 / 더블 점프 |
| 좌클릭 | 일반 공격 |
| 우클릭 | 강공격 |
| E | 연타 |
| Q | 궁극기: 비궁극기 명중 7회로 완충 |
| V / B | 임시 좌클릭 / 우클릭 공격 대체 키 |
| Esc | 일시정지 메뉴 |
| F1 | 디버그 HUD |
| Left Alt 누르기 | 메뉴 포인터 표시 |

## 프로젝트 구성

- `Source`: 전투 및 HUD C++ 구현
- `Content/ComicCombat`: 맵, 머티리얼, 애니메이션, VFX, UI 에셋
- `Tools/ComicCombat`: 에셋 제작 및 편집 스크립트
- `SourceArt`: 원본 이미지와 제작 자료

에셋과 원본 이미지는 Git LFS로 관리합니다. `Binaries`, `Intermediate`, `Saved`, `DerivedDataCache` 등 재생성 가능한 파일은 커밋하지 않습니다. 개인 인증 설정은 Git에서 제외되는 `Config/UserEngine.ini`에 보관합니다.
