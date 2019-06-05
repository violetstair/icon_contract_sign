# ICON Loopchain Contract Sign

트랜젝션을 컨트랙트 내부에서 재처리 하는 컨트랙트 PoC

## 개요
사용자가 자신의 PC에서 signing한 데이터를 API에 전달하고 API에서는 API가 보유하고 있는 해당 사용자의 wallet으로 대리 signing해서 transaction을 발생시킨다.

### 실행 방법
```bash
tbears test contract_sign/
```

## 이슈사항
test code의 setUp()에서 self.icon_service를 None으로 하면 원하는 결과를 얻을 수 있지만, IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))를 추가하면
signing된 transaction 데이터를 컨트랙트에 전송할 때 `Out of balance: balance` 에러가 발생하며 Contract 실행이 되지 않는다.

## 실행 환경
Docker iconloop/tbears:1.2.0-rc1 (image id : adcb46bbc201)

