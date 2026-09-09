/**
 * Tistory 로그인 & 글쓰기 페이지 접근 테스트
 *
 * [1단계] 세션 저장 (최초 1회 + 세션 만료 시)
 *   node test_tistory_login.js --save-session
 *   → 브라우저가 열리면 직접 로그인 + 2FA 완료 후 Enter
 *
 * [2단계] 저장된 세션으로 실행
 *   node test_tistory_login.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

require('dotenv').config();

const BLOG = process.env.TISTORY_BLOG; // subdomain만 (예: yuchung)
const SESSION_FILE = path.join(__dirname, 'tistory_session.json');
const SAVE_SESSION = process.argv.includes('--save-session');

const KAKAO_LOGIN_URL = 'https://accounts.kakao.com/login/?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize%3Fclient_id%3D3e6ddd834b023f24221217e370daed18%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%252Fredirect%26response_type%3Dcode%26through_account%3Dtrue';
const WRITE_URL = `https://${BLOG}.tistory.com/manage/newpost`;
const MANAGE_URL = `https://${BLOG}.tistory.com/manage`;

function waitForEnter(message) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(message, () => { rl.close(); resolve(); });
  });
}

(async () => {
  if (!BLOG) {
    console.error('❌ .env에 TISTORY_BLOG를 설정해주세요');
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: false, slowMo: 300 });

  try {
    // ── 1단계: 세션 저장 모드 ──────────────────────────────
    if (SAVE_SESSION) {
      console.log('🔑 세션 저장 모드');
      console.log('   브라우저에서 직접 로그인 + 2FA를 완료해주세요.');
      const context = await browser.newContext();
      const page = await context.newPage();
      await page.goto(KAKAO_LOGIN_URL, { waitUntil: 'domcontentloaded' });

      await waitForEnter('\n✋ 로그인과 2FA를 완료한 후 Enter를 눌러주세요...');

      await context.storageState({ path: SESSION_FILE });
      console.log(`✅ 세션 저장 완료: ${SESSION_FILE}`);
      await browser.close();
      return;
    }

    // ── 2단계: 저장된 세션으로 실행 ───────────────────────
    if (!fs.existsSync(SESSION_FILE)) {
      console.error('❌ 저장된 세션이 없습니다. 먼저 --save-session 으로 로그인해주세요.');
      process.exit(1);
    }

    console.log('🚀 저장된 세션으로 시작');
    const context = await browser.newContext({ storageState: SESSION_FILE });
    const page = await context.newPage();

    // 관리 페이지 접근 (세션 유효성 확인)
    console.log(`\n📋 관리 페이지 접근 중: ${MANAGE_URL}`);
    await page.goto(MANAGE_URL, { waitUntil: 'networkidle', timeout: 15000 });
    console.log('   현재 URL:', page.url());

    if (!page.url().includes('/manage')) {
      console.error('❌ 세션이 만료된 것 같습니다. --save-session 으로 다시 로그인해주세요.');
      await browser.close();
      process.exit(1);
    }
    console.log('✅ 관리 페이지 접근 성공!');

    // 글쓰기 페이지 접근
    console.log(`\n✏️  글쓰기 페이지 접근 중: ${WRITE_URL}`);
    await page.goto(WRITE_URL, { waitUntil: 'networkidle', timeout: 15000 });
    console.log('   현재 URL:', page.url());
    const isWritePage = page.url().includes('/manage/newpost') || page.url().includes('/manage/post');
    console.log(isWritePage ? '✅ 글쓰기 페이지 접근 성공!' : '⚠️  글쓰기 페이지 접근 실패');

    await page.screenshot({ path: 'tistory_write_page.png', fullPage: true });
    console.log('\n📸 스크린샷 저장: tistory_write_page.png');

  } catch (err) {
    console.error('\n❌ 오류 발생:', err.message);
  } finally {
    await browser.close();
  }
})();
