/**
 * Tistory 글 발행 테스트
 * - 저장된 세션으로 글쓰기 페이지 접근
 * - 기본 모드 → HTML 모드 전환 후 refined_post 삽입
 * - 임시저장으로 마무리 (실수로 발행 방지)
 *
 * 사용법: node test_tistory_post.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { TEST_POST } = require('./test_post_data');

require('dotenv').config();

const BLOG = process.env.TISTORY_BLOG;
const SESSION_FILE = path.join(__dirname, 'tistory_session.json');
const WRITE_URL = `https://${BLOG}.tistory.com/manage/newpost`;

(async () => {
  if (!fs.existsSync(SESSION_FILE)) {
    console.error('❌ 세션 파일 없음. 먼저 --save-session 으로 로그인해주세요.');
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: false, slowMo: 300 });
  const context = await browser.newContext({ storageState: SESSION_FILE });
  const page = await context.newPage();

  try {
    // 1. 글쓰기 페이지 이동
    console.log('✏️  글쓰기 페이지 이동 중...');
    await page.goto(WRITE_URL, { waitUntil: 'networkidle', timeout: 15000 });
    console.log('   현재 URL:', page.url());

    // 2. 제목 입력
    console.log('📝 제목 입력 중...');
    const titleInput = page.locator('#post-title-inp');
    await titleInput.waitFor({ timeout: 8000 });
    await titleInput.click();
    await titleInput.fill(TEST_POST.title);
    console.log('   제목:', TEST_POST.title);

    // 3. 모드 드롭다운 열기 ("기본모드" 버튼)
    console.log('🔀 HTML 모드 전환 중...');
    await page.locator('#editor-mode-layer-btn-open').click();
    await page.waitForTimeout(500);

    // 4. alert 리스너 등록 후 "HTML" 클릭
    page.once('dialog', async (dialog) => {
      console.log('   다이얼로그:', dialog.message());
      await dialog.accept();
    });
    await page.locator('#editor-mode-html').click();
    await page.waitForTimeout(1500); // alert 처리 + 모드 전환 대기
    console.log('   HTML 모드 전환 완료');

    // 6. CodeMirror에 HTML 콘텐츠 삽입
    console.log('📄 HTML 콘텐츠 삽입 중...');
    await page.waitForSelector('.CodeMirror', { timeout: 8000 });
    await page.evaluate((html) => {
      const cmEl = document.querySelector('.CodeMirror');
      if (cmEl && cmEl.CodeMirror) {
        cmEl.CodeMirror.setValue(html);
      }
    }, TEST_POST.content);
    await page.waitForTimeout(800);
    console.log('   콘텐츠 삽입 완료');

    // 7. 기본모드로 복귀 (HTML 내용을 에디터에 반영)
    console.log('🔀 기본모드로 복귀 중...');
    await page.locator('#editor-mode-layer-btn-open').click();
    await page.waitForTimeout(500);
    page.once('dialog', async (dialog) => {
      console.log('   다이얼로그:', dialog.message());
      await dialog.accept();
    });
    await page.locator('#editor-mode-kakao').click();
    await page.waitForTimeout(1500);
    console.log('   기본모드 복귀 완료');

    // 8. 스크린샷으로 상태 확인
    await page.screenshot({ path: 'tistory_post_preview.png', fullPage: true });
    console.log('\n📸 미리보기 스크린샷 저장: tistory_post_preview.png');

    // 9. 임시저장
    console.log('\n💾 임시저장 중...');
    const saveBtn = page.locator('span.btn-draft a.action');
    await saveBtn.click();
    await page.waitForTimeout(1500);
    console.log('✅ 임시저장 완료!');

  } catch (err) {
    console.error('\n❌ 오류 발생:', err.message);
    await page.screenshot({ path: 'tistory_post_error.png' });
    console.log('📸 에러 스크린샷 저장: tistory_post_error.png');
  } finally {
    await browser.close();
  }
})();
