[Google Ai Studio 에서 structure 설계 진행] = structure-writer - 새 채팅창

다음 기술스택을 참고해, layered architecture와 solid principle을 준수한 codebase structure 제안해주세요.
directory structure, top level building blocks를 포함하세요.

---
<사용_기술_스택> /docs/techstack.md

---
<페르소나> /docs/persona.md

---
<프로젝트_요구사항> /docs/requirement.md

---

반드시 판단 기준을 따르세요.
1. presentation은 반드시 business logic과 분리되어야합니다.
2. pure business logic은 반드시 persistence layer와 분리되어야합니다.
3. internal logic은 반드시 외부연동 contract, caller와 분리되어야합니다.
4. 하나의 모듈은 반드시 하나의 책임을 가져야합니다.


------------------------------------------------------------------------------
[Google Ai Studio 에서 structure 검증 진행] = structure-critic - 기존 채팅창

이 내용이 정말 확장성있고 코드가 정돈된채로, 기능을 하나하나 추가하기 좋은 구조인지 점검하세요.
또한, 순수함수들에 대해 단위테스트를 추가할 것입니다. 여기에도 최적화된 좋은 구조인지 엄격하게 검증하세요. 최대한 깐깐한 기준으로 평가해야합니다.


------------------------------------------------------------------------------
[Google Ai Studio 에서 structure 문서화 진행] - 기존 채팅창

좋습니다. 이를 반영해서 codebase structure 최종본을 만들어주세요.