import { test, expect, type Page } from '@playwright/test';

async function begin(page: Page, persist = true) {
  await page.goto('/');
  await page.getByLabel('Tôi từ 18 tuổi trở lên.').check();
  await page.getByLabel(/Tôi hiểu đang tương tác với AI/).check();
  if (persist) await page.getByLabel(/Lưu lịch sử có mã hóa/).check();
  await page.getByRole('button', { name: /Bắt đầu khoảng riêng/ }).click();
  await expect(page.getByRole('heading', { name: /Hôm nay/ })).toBeVisible();
}

test('mood, reframing, feedback, persistence, export and delete', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await begin(page);
  await page.screenshot({ path: 'test-results/cogai-desktop.png', fullPage: true });
  await page.getByRole('button', { name: /Khá dễ chịu/ }).click();
  await page.getByLabel('Ghi chú cảm xúc').fill('Hôm nay tôi hoàn thành một việc nhỏ.');
  await page.getByRole('button', { name: 'Ghi nhận', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Đã lưu');
  await page.getByRole('button', { name: 'Nhìn lại suy nghĩ', exact: true }).click();
  await page.getByRole('button', { name: 'Dùng ví dụ' }).click();
  await page.getByRole('button', { name: /Cùng nhìn lại/ }).click();
  await expect(page.getByText('Điều đã biết & điều còn mở')).toBeVisible();
  await expect(page.getByText(/Một tình huống khó chưa nói lên/)).toBeVisible();
  await page.getByLabel('Bạn muốn điều chỉnh gì?').fill('Viết gần gũi hơn');
  await page.getByRole('button', { name: 'Thử điều chỉnh góc nhìn' }).click();
  await expect(page.getByLabel('Bạn muốn điều chỉnh gì?')).toHaveValue('');
  await page.getByRole('button', { name: 'Mức hữu ích 4 trên 5', exact: true }).click();
  await page.getByRole('button', { name: 'Gửi phản hồi', exact: true }).click();
  await expect(page.getByText('Đã lưu phản hồi', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Nhật ký của tôi', exact: true }).click();
  await expect(page.getByText('Hôm nay tôi hoàn thành một việc nhỏ.')).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Nhật ký của tôi', exact: true }).click();
  await expect(page.getByText('Hôm nay tôi hoàn thành một việc nhỏ.')).toBeVisible();
  const downloaded = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Xuất dữ liệu', exact: true }).click();
  expect((await downloaded).suggestedFilename()).toBe('cogai-du-lieu-phien.json');
  await page.getByRole('button', { name: 'Xóa dữ liệu phiên' }).click();
  await page.getByRole('button', { name: 'Xóa & kết thúc', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Trước khi bắt đầu' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('question nine triggers support regardless of a low total', async ({ page }) => {
  await begin(page, false);
  await page.getByRole('button', { name: 'Sàng lọc', exact: true }).click();
  for (let index = 0; index < 8; index++) {
    await page.getByRole('button', { name: /Không ngày nào/ }).click();
    await page.getByRole('button', { name: /Tiếp theo/ }).click();
  }
  await page.getByRole('button', { name: /Vài ngày/ }).click();
  await expect(page.getByText(/Không cần chờ hoàn tất/)).toBeVisible();
  await page.getByRole('button', { name: 'Xem mức điểm' }).click();
  await expect(page.getByText(/Câu trả lời ở mục 9/)).toBeVisible();
  await expect(page.getByText('Mức điểm: Tối thiểu', { exact: true })).toBeVisible();
});

test('mobile layout, chat and independent risk branch', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await begin(page, false);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/cogai-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Mở menu' }).click();
  await page.getByRole('button', { name: 'Trò chuyện', exact: true }).click();
  await page.getByLabel('Tin nhắn của bạn').fill('Mình lo về công việc.');
  await page.getByRole('button', { name: 'Gửi tin nhắn' }).click();
  await expect(page.getByText(/Trong chuyện vừa kể/)).toBeVisible();
  await page.getByLabel('Tin nhắn của bạn').fill('Tôi muốn chết');
  await page.getByRole('button', { name: 'Gửi tin nhắn' }).click();
  await expect(page.getByRole('heading', { name: 'Bạn có thể tìm người ở bên' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
