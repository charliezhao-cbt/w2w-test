#!/usr/bin/env python3
"""Send a W2W sample status email through a configured SMTP relay.
Environment: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_TO, optional MAIL_FROM and W2W_ACTIONS_URL.
Never logs credentials, sends only to explicitly configured recipients.
"""
import os, json, pathlib, smtplib, ssl, html
from email.message import EmailMessage
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'actions' / 'data' / 'items.json'

def report():
    records=json.loads(DATA.read_text(encoding='utf-8')).get('items',[])
    counts=Counter(str(x.get('signal') or '확인 필요') for x in records)
    w46=[x for x in records if x.get('week')=='W46']
    week=sorted({x.get('week','') for x in records})[-1] if records else '없음'
    now=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M')
    lines=[f'W2W Action Item 현황 ({now} KST)', '',f'전체: {len(records)}건 / 최신 발생 주차: {week}',
           f'🔵 완료 {counts["완료"]} / 🟢 진행 중 {counts["진행 중"]} / 🟡 확인 필요 {counts["확인 필요"]} / 🔴 지연 {counts["지연"]}',
           '',f'W46 신규 과제: {len(w46)}건']
    for x in w46: lines.append(f'- {x.get("title","")} | {x.get("owner", "미확정")} | {x.get("due", "미확정")}')
    lines += ['', '주의: 현재는 가상의 회의록을 활용한 자동화 테스트입니다.',
              '이 보고서는 관리자 검토 전의 Action Item 후보를 포함할 수 있습니다.']
    page=os.getenv('W2W_ACTIONS_URL','').strip()
    if page:lines.extend(['',f'Action Item 페이지: {page}'])
    return '\n'.join(lines),week

def main():
    envs=('SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASSWORD','MAIL_TO')
    missing=[v for v in envs if not os.getenv(v)]
    if missing:raise SystemExit('Missing SMTP settings: '+', '.join(missing))
    host=os.environ['SMTP_HOST'];port=int(os.environ['SMTP_PORT']);username=os.environ['SMTP_USER'];password=os.environ['SMTP_PASSWORD']
    to=[x.strip() for x in os.environ['MAIL_TO'].split(',') if x.strip()]
    if not to:raise SystemExit('MAIL_TO is empty')
    body,week=report()
    msg=EmailMessage()
    msg['Subject']=f'[W2W 테스트] {week} Action Item 현황'
    msg['From']=os.getenv('MAIL_FROM') or username
    msg['To']=', '.join(to)
    msg.set_content(body)
    if port==465:
        with smtplib.SMTP_SSL(host,port,timeout=40,context=ssl.create_default_context()) as client:
            client.login(username,password);client.send_message(msg)
    else:
        with smtplib.SMTP(host,port,timeout=40) as client:
            client.ehlo();client.starttls(context=ssl.create_default_context());client.ehlo()
            client.login(username,password);client.send_message(msg)
    print(f'Mail submitted to SMTP server for {len(to)} recipient(s); latest week {week}.')

if __name__=='__main__':main()
