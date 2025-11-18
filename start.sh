#!/bin/bash
# Railway startup script (Combined and Corrected)

# 1. (기존 설정 유지) Production settings 설정
# 이 부분이 있어야 Railway 환경에서 올바른 설정으로 앱이 실행됩니다.
export DJANGO_SETTINGS_MODULE=config.settings.production

# 2. (새로 추가) SQLite 파일 존재 보장
# /data 볼륨에 db.sqlite3 파일이 있도록 하여 'unable to open' 오류를 방지합니다.
touch /data/db.sqlite3

# 3. (새로 추가) 데이터베이스 마이그레이션 실행
# 앱 실행 전, 데이터베이스 테이블을 최신 상태로 준비합니다.
echo "Running database migrations..."
python manage.py migrate --noinput

# 4. (기존 설정 유지) 정적 파일 수집 (Static files)
# CSS, JS 같은 정적 파일들을 한 곳으로 모읍니다.
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 5. (기존 설정 유지) Gunicorn 웹 서버 시작
# 최종적으로 웹 서버를 실행하여 외부 요청을 받을 수 있게 합니다.
# exec는 프로세스 관리를 더 효율적으로 만들어줍니다.
echo "Starting gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT