import type { AdminCollectorStatusResponse } from '../types/adminCollector.js';

const generatedAt = '2026-08-26T01:00:00Z';

export const MOCK_ADMIN_COLLECTOR_STATUS: AdminCollectorStatusResponse = {
  generated_at: generatedAt,
  queue: {
    queue_name: 'collection',
    broker_available: true,
    worker_available: true,
    worker_count: 1,
  },
  schedule: {
    enabled: false,
    source_id: 'youthcenter-api',
    requested_count: 100,
    complete_snapshot: false,
    cron_hour: 3,
    cron_minute: 0,
    timezone: 'Asia/Seoul',
  },
  collectors: [
    ['bokjiro-central-welfare-api', '복지로 중앙부처 복지서비스', 'api', 'ready', 'configured', 461],
    ['cheonan-youthcenter-web', '천안청년센터이음 공지사항', 'web', 'ready', 'not_required', 0],
    ['data-go-kr-incheon-youth-programs', '인천광역시 청년공간 유유기지 프로그램', 'file', 'ready', 'not_required', 4],
    ['kinfa-financial-product-web', '서민금융진흥원 금융상품', 'web', 'ready', 'not_required', 0],
    ['kosaf-scholarship-web', '한국장학재단 장학금', 'web', 'ready', 'not_required', 0],
    ['kpass-transit-refund-web', '모두의카드 교통비 환급', 'web', 'ready', 'not_required', 0],
    ['lh-housing-announcement-web', 'LH청약플러스 임대주택 공고', 'web', 'ready', 'not_required', 0],
    ['regional-busan-youth-platform', '부산청년플랫폼', 'web', 'ready', 'not_required', 0],
    ['regional-gyeongbuk-youth-platform', '경북청년포털 청년e끌림', 'web', 'ready', 'not_required', 0],
    ['work24-policy-web', '고용24 정책', 'web', 'ready', 'not_required', 0],
    ['youthcenter-api', '온통청년 청년정책 API', 'api', 'configuration_required', 'missing', 1587],
  ].map(([source_id, display_name, source_type, runtime_status, credential_status, public_policy_count]) => ({
    source_id,
    display_name,
    source_type,
    manual_run_enabled: true,
    runtime_status,
    worker_registered: true,
    credential_status,
    public_policy_count,
    active_run: null,
    last_run: null,
  })) as AdminCollectorStatusResponse['collectors'],
};
