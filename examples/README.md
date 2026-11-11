<!-- Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
Derived from Tortoise ORM; maintained and modified for Rakko ORM.
SPDX-License-Identifier: Apache-2.0 -->

# Rakko ORM 예제

프로젝트 루트에서 실행합니다. Python 3.12 이상이 필요합니다.

```powershell
uv run -m examples.basic
uv run -m examples.queries
uv run -m examples.relations
uv run -m examples.bulk_and_transactions
```

각 예제는 독립적인 메모리 SQLite DB를 생성하고, 종료할 때 연결을 정리합니다.

| 파일 | 내용 |
| --- | --- |
| `basic.py` | `Field[T]`, `@meta`, nullable 필드, 생성·조회·부분 수정·삭제 |
| `models.py` | 관계형 예제의 공통 모델과 `@reverse_relation` 선언 |
| `queries.py` | 연산자 조건식, 필드 기반 정렬·조회, 표현식·집계, 부분 모델, JSON·Text |
| `relations.py` | FK 조건식, JOIN을 통한 관계 로딩, 역참조, 필터가 있는 prefetch |
| `bulk_and_transactions.py` | bulk 생성·수정, 생성자 타입을 유지하는 upsert, 필드 키 매핑, 트랜잭션 |
| `mysql_sql.py` | MySQL UNSIGNED·AUTO_INCREMENT 스키마와 SELECT·UPDATE SQL 미리보기 |

MySQL SQL 예제는 드라이버만 필요하며, DB 서버에 연결하거나 SQL을 실행하지 않습니다.

```powershell
uv run --extra aiomysql -m examples.mysql_sql
```

`User.id` 같은 클래스 속성은 쿼리 표현식이고, `user.id` 같은 인스턴스 속성은 실제 값입니다.
조건식은 `&`, `|`, `~`로 조합하며, 내림차순 정렬에는 `-Member.age`를 사용합니다.

`create`의 연결 인자는 첫 번째 위치 인자로 전달하거나 `.using_db(connection)`으로 지정합니다.
`update`는 전달한 필드만 변경합니다. 일반 필드는 생성자의 선택 인자로 표시되지만,
생성·저장 시의 값 검증과 DB 제약 조건은 적용됩니다.

예제 실행 검증을 포함한 전체 테스트:

```powershell
uv run --all-groups --extra asyncpg --extra psycopg pytest -q
```
