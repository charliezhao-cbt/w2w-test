#!/usr/bin/env python3
"""Email the complete W2W Action Item table as HTML + plain text.

Required GitHub Secrets: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_TO.
Optional: MAIL_FROM, W2W_ACTIONS_URL. Python 3.11+; stdlib only.
"""
import html
import json
import os
import pathlib
import re
import smtplib
import socket
import ssl
import sys
from collections import Counter
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'actions' / 'data' / 'items.json'
DEFAULT_ACTIONS_URL = 'https://charliezhao-cbt.github.io/w2w-test/actions/'
COLUMNS = [
    ('week', '발생 주차'), ('title', '제목'), ('content', '내용'),
    ('department', '담당부서'), ('owner', '담당자'), ('due', '납기'),
    ('signal', '신호등'), ('progress', '진행 사항'),
]
SIGNALS = {
    '완료': ('🔵 완료', '#2563eb'),
    '진행 중': ('🟢 진행 중', '#16a34a'),
    '확인 필요': ('🟡 확인 필요', '#ca8a04'),
    '지연': ('🔴 지연', '#dc2626'),
}


def read_items():
    if not DATA.exists():
        raise FileNotFoundError(f'Action Item JSON 파일이 없습니다: {DATA}')
    obj = json.loads(DATA.read_text(encoding='utf-8-sig'))
    records = obj.get('items') if isinstance(obj, dict) else None
    if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
        raise ValueError('items.json의 items가 객체의 배열이어야 합니다.')
    return records


def latest_week(records):
    weeks = [str(x.get('week', '')) for x in records]
    def key(w):
        m = re.fullmatch(r'W(\d+)', w)
        return int(m.group(1)) if m else -1
    return max(weeks, key=key, default='없음')


def value(item, key):
    v = item.get(key)
    if v is None or str(v).strip() == '':
        return '미입력' if key == 'progress' else ('미확정' if key in ('owner', 'department', 'due') else '-')
    return str(v).strip()


def render(records):
    week = latest_week(records)
    now = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M')
    counts = Counter(str(item.get('signal') or '확인 필요') for item in records)
    summary = (f'전체 {len(records)}건 | 완료 {counts["완료"]} | 진행 중 {counts["진행 중"]} | '
               f'확인 필요 {counts["확인 필요"]} | 지연 {counts["지연"]}')
    page = os.getenv('W2W_ACTIONS_URL', '').strip() or DEFAULT_ACTIONS_URL
    # Plain text is included for clients that block HTML.
    plain = [f'[W2W] Action Item 전체 현황 ({now} KST)', summary, f'최신 발생 주차: {week}', '']
    plain.append(' | '.join(label for _, label in COLUMNS))
    for item in records:
        plain.append(' | '.join(value(item, key).replace('\n', ' ') for key, _ in COLUMNS))
    plain += ['', f'관리 페이지: {page}', '※ 가상 회의록을 활용한 테스트 데이터이며 관리자 검토 전 후보가 포함될 수 있습니다.']

    e = lambda s: html.escape(str(s), quote=True)
    head = ''.join(f'<th style="{TH_STYLE}">{e(label)}</th>' for _, label in COLUMNS)
    rows = []
    for i, item in enumerate(records):
        cells = []
        for key, _ in COLUMNS:
            content = value(item, key)
            if key == 'signal':
                label, color = SIGNALS.get(content, (content, '#334155'))
                body = f'<span style="color:{color};font-weight:bold">{e(label)}</span>'
            else:
                body = e(content).replace('\n', '<br>')
            cells.append(f'<td style="{TD_STYLE};background:{"#f8fafc" if i % 2 else "#fff"}">{body}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    table = (f'<table role="presentation" cellspacing="0" cellpadding="0" '
             f'style="border-collapse:collapse;width:100%;font-size:13px;line-height:1.5">'
             f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>')
    html_body = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#f3f6fa;font-family:Arial,'Malgun Gothic',sans-serif;color:#14223b">
<div style="max-width:1200px;margin:auto;padding:24px;background:#fff;border:1px solid #e2e8f0;border-radius:12px">
  <h1 style="font-size:25px;margin:0 0 8px">W2W Action Item 전체 현황</h1>
  <p style="color:#64748b;margin:0 0 16px">{e(now)} KST · 최신 발생 주차 {e(week)}</p>
  <p style="font-size:14px;font-weight:bold;margin:0 0 16px">{e(summary)}</p>
  <p style="margin:0 0 16px"><a href="{e(page)}" style="color:#1d4ed8">Action Item 관리 페이지 열기</a></p>
  <div style="overflow-x:auto">{table}</div>
  <p style="font-size:12px;color:#64748b;margin-top:20px">가상 회의록 기반 자동화 테스트이며, 관리자 검토 전 후보가 포함될 수 있습니다. 이 메일은 읽기 전용입니다.</p>
</div></body></html>'''
    return '\n'.join(plain), html_body, week


TH_STYLE = 'background:#eaf0f8;color:#132342;font-weight:bold;text-align:left;padding:10px;border:1px solid #dbe4ef;white-space:nowrap;'
TD_STYLE = 'vertical-align:top;padding:10px;border:1px solid #e2e8f0;word-break:break-word;'


def main():
    required = ('SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'MAIL_TO')
    missing = [x for x in required if not os.getenv(x, '').strip()]
    if missing:
        sys.exit('[설정 오류] GitHub Repository Secrets 누락: ' + ', '.join(missing))
    host = os.environ['SMTP_HOST'].strip()
    try:
        port = int(os.environ['SMTP_PORT'].strip())
        if not (1 <= port <= 65535):
            raise ValueError('out of range')
    except ValueError:
        sys.exit('[설정 오류] SMTP_PORT는 유효한 포트 번호여야 합니다.')
    username = os.environ['SMTP_USER'].strip()
    password = os.environ['SMTP_PASSWORD'].strip()
    recipients = [v.strip() for v in os.environ['MAIL_TO'].split(',') if v.strip()]
    if not recipients:
        sys.exit('[설정 오류] MAIL_TO가 비어 있습니다.')
    try:
        records = read_items()
        plain, html_body, week = render(records)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.exit(f'[데이터 오류] {type(exc).__name__}: {exc}')
    msg = EmailMessage()
    msg['Subject'] = f'[W2W] {week} Action Item 전체 현황 ({len(records)}건)'
    msg['From'] = os.getenv('MAIL_FROM', '').strip() or username
    msg['To'] = ', '.join(recipients)
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype='html')
    try:
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=35, context=context) as smtp:
                smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=35) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(username, password)
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        sys.exit(f'[인증 오류] SMTP 인증 실패 (코드 {exc.smtp_code}). 앱 비밀번호를 확인하세요.')
    except (smtplib.SMTPException, OSError, socket.timeout) as exc:
        sys.exit(f'[발송 오류] {type(exc).__name__}: 메일 서버 및 연결 설정을 확인하세요.')
    print(f'[성공] HTML Action Item 표 {len(records)}건을 SMTP 서버에 접수했습니다. 최신 주차 {week}, 받는 사람 {len(recipients)}명.')


if __name__ == '__main__':
    main()
