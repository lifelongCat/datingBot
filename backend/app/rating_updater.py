from celery import Celery
from celery.schedules import crontab
from sqlalchemy import text

from app.config import settings
from app.database import sync_session_maker

celery = Celery(
    'rating_tasks',
    broker=settings.RABBITMQ_URL
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

RATING_WEIGHTS = {
    'primary': 0.4,
    'behavioral': 0.5,
    'referral': 0.1
}


def calculate_primary_rating(telegram_id: int) -> float:
    with sync_session_maker() as session:
        result = session.execute(text(f'''
            SELECT (
                CASE
                    WHEN age < 18 OR age > 100 THEN 0
                    ELSE 1
                END +
                CASE
                    WHEN length(interests) < 3 THEN 0
                    WHEN length(interests) BETWEEN 3 AND 10 THEN 1
                    ELSE 2
                END +
                CASE
                    WHEN length(city) < 3 THEN 0
                    ELSE 1
                END
            ) as rating
            FROM users
            WHERE telegram_id = {telegram_id};
        '''))
        return float(result.scalar())


def calculate_behavioral_rating(telegram_id: int) -> float:
    with sync_session_maker() as session:
        result = session.execute(text(f'''
            WITH user_likes_skips_rating AS (
                SELECT
                    count(*) FILTER (WHERE is_like IS TRUE) -
                    count(*) FILTER (WHERE is_like IS FALSE)
                as rating
                FROM user_interactions
                WHERE responser_telegram_id = {telegram_id}
            ), user_mutual_likes_rating AS (
                SELECT count(*) AS rating
                FROM user_interactions ui1
                JOIN user_interactions ui2 ON
                    ui1.requester_telegram_id = ui2.responser_telegram_id
                    AND ui1.responser_telegram_id = ui2.requester_telegram_id
                WHERE ui1.responser_telegram_id = {telegram_id}
                    AND ui1.is_like = True
                    AND ui2.is_like = True
            ), user_start_dialogue_rating AS (
                SELECT (
                    count(*) FILTER (WHERE is_checked IS TRUE) /
                    greatest(count(*) FILTER (WHERE is_checked IS FALSE), 1)
                ) as rating
                FROM user_interactions
                WHERE responser_telegram_id = {telegram_id}
            ), user_last_activity_rating AS (
                SELECT
                    CASE
                        WHEN extract(days from now() - last_activity) < 1 THEN 5
                        WHEN extract(days from now() - last_activity) < 15 THEN 4
                        WHEN extract(months from now() - last_activity) < 1 THEN 3
                        WHEN extract(months from now() - last_activity) < 3 THEN 2
                        WHEN extract(months from now() - last_activity) < 6 THEN 1
                        ELSE 0
                    END
                as rating
                FROM users
                WHERE telegram_id = {telegram_id}
            )

            SELECT
                (SELECT rating FROM user_likes_skips_rating) +
                (SELECT rating FROM user_mutual_likes_rating) +
                (SELECT rating FROM user_start_dialogue_rating) +
                (SELECT rating FROM user_last_activity_rating)
            AS total_rating;
        '''))
        return float(result.scalar())


def calculate_referals_rating(telegram_id: int) -> float:
    with sync_session_maker() as session:
        result = session.execute(text(f'''
            SELECT count(*) * 0.2 as rating
            FROM users
            WHERE referal_id = {telegram_id}
        '''))
        return float(result.scalar())


def calculate_combined_rating(
    primary_rating: float, behavioral_rating: float, referals_rating: float
) -> float:
    return (
        primary_rating * RATING_WEIGHTS['primary'] +
        behavioral_rating * RATING_WEIGHTS['behavioral'] +
        referals_rating * RATING_WEIGHTS['referral']
    )


@celery.task
def update_user_ratings():
    with sync_session_maker() as session:
        result = session.execute(text('SELECT telegram_id FROM users;'))
        for telegram_id in result.scalars().all():
            primary_rating = calculate_primary_rating(telegram_id)
            behavioral_rating = calculate_behavioral_rating(telegram_id)
            referals_rating = calculate_referals_rating(telegram_id)
            combined_rating = calculate_combined_rating(
                primary_rating,
                behavioral_rating,
                referals_rating
            )
            session.execute(text(f'''
                UPDATE user_ratings
                SET rating = {combined_rating}
                WHERE telegram_id = {telegram_id}
            '''))
        session.commit()


celery.conf.beat_schedule = {
    'update-ratings-every-hour': {
        'task': 'app.rating_updater.update_user_ratings',
        # 'schedule': crontab(hour='*', minute=0),
        'schedule': crontab(minute='*'),
    },
}
