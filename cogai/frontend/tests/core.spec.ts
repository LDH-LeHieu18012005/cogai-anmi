import { test, expect } from '@playwright/test';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

test('durable alias login, server context, revocable consent and account deletion', async ({page})=>{
  await page.goto('/');
  await page.getByLabel('Tôi từ 18 tuổi trở lên.').check();
  await page.getByLabel(/Tôi hiểu đang tương tác với AI/).check();
  await page.getByLabel(/Lưu lịch sử có mã hóa/).check();
  await page.getByRole('button',{name:/Bắt đầu khoảng riêng/}).click();
  await page.getByRole('button',{name:'Tài khoản & quyền dữ liệu',exact:true}).click();
  const alias='test-'+Date.now();
  await page.getByLabel('Bí danh mới').fill(alias);
  await page.getByLabel('Mật khẩu mới').fill('browser-test-password-123');
  await page.getByRole('button',{name:'Tạo tài khoản bí danh',exact:true}).click();
  await expect(page.getByText(`Bí danh: ${alias}`,{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await page.getByLabel('Tin nhắn của bạn').fill('Tôi lo về kỳ thi ngày mai.');
  await page.getByRole('button',{name:'Gửi tin nhắn'}).click();
  await expect(page.getByText(/Trong chuyện vừa kể/)).toBeVisible();
  await page.reload();
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await expect(page.getByText('Tôi lo về kỳ thi ngày mai.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Tài khoản & quyền dữ liệu',exact:true}).click();
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();
  await page.getByText('Đã có tài khoản bí danh? Đăng nhập',{exact:true}).click();
  await page.getByLabel('Bí danh đăng nhập').fill(alias);
  await page.getByLabel('Mật khẩu đăng nhập').fill('browser-test-password-123');
  await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await expect(page.getByText('Tôi lo về kỳ thi ngày mai.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Tài khoản & quyền dữ liệu',exact:true}).click();
  await page.getByLabel('Lưu lịch sử và ngữ cảnh').uncheck();
  await page.getByRole('button',{name:'Lưu lựa chọn đồng ý',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('Đã cập nhật');
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await expect(page.getByText('Tôi lo về kỳ thi ngày mai.',{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Tài khoản & quyền dữ liệu',exact:true}).click();
  await page.getByLabel('Tôi muốn xóa tài khoản và toàn bộ dữ liệu hoạt động').check();
  await page.getByRole('button',{name:'Xóa tài khoản',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Trước khi bắt đầu'})).toBeVisible();
});

test('clarification resumes chat but high safety survives a reset',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Tôi từ 18 tuổi trở lên.').check();
  await page.getByLabel(/Tôi hiểu đang tương tác với AI/).check();
  await page.getByRole('button',{name:/Bắt đầu khoảng riêng/}).click();
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await page.getByLabel('Tin nhắn của bạn').fill('Tôi không muốn tiếp tục nữa');
  await page.getByRole('button',{name:'Gửi tin nhắn'}).click();
  await expect(page.getByRole('heading',{name:'Làm rõ điều bạn muốn dừng'})).toBeVisible();
  await page.getByLabel('Bạn muốn làm rõ điều gì?').fill('Tôi muốn dừng bài tập vì mệt, tôi đang ở cùng bạn');
  await page.getByLabel(/Tôi đang không gặp nguy hiểm trước mắt/).check();
  await page.getByRole('button',{name:'Gửi lời làm rõ'}).click();
  await expect(page.getByRole('heading',{name:'Làm rõ điều bạn muốn dừng'})).toHaveCount(0);
  await page.getByLabel('Tin nhắn của bạn').fill('Tôi muốn chết');
  await page.getByRole('button',{name:'Gửi tin nhắn'}).click();
  await expect(page.getByRole('heading',{name:'Bạn có thể tìm người ở bên'})).toBeVisible();
  await page.getByRole('button',{name:/Cuộc trò chuyện mới/}).click();
  await expect(page.getByRole('heading',{name:'Bạn có thể tìm người ở bên'})).toBeVisible();
});

test('expert sees only shared summary, accepts explicitly and loses withdrawn access',async({page,browser})=>{
  const alias='expert-'+Date.now();
  const professional=await browser.newContext();
  try{
    await page.request.post('/api/session',{data:{accepted:true,adult:true,persist:true}});
    await page.goto('/');
    await page.getByRole('button',{name:'Tìm người hỗ trợ',exact:true}).click();
    await page.getByLabel('Tóm tắt bạn muốn chia sẻ').fill('Tóm tắt giả lập chỉ chia sẻ cho người tiếp nhận');
    await page.getByLabel('Tôi đồng ý chia sẻ tóm tắt này với người tiếp nhận được cấp quyền.').check();
    await page.getByRole('button',{name:'Tạo yêu cầu hỗ trợ',exact:true}).click();
    await expect(page.getByText('Đang chờ người tiếp nhận',{exact:true})).toBeVisible();
    await professional.request.post('http://127.0.0.1:5173/api/session',{data:{accepted:true,adult:true,persist:true}});
    const registered=await professional.request.post('http://127.0.0.1:5173/api/account',{data:{alias,password:'synthetic-expert-password-123'}});
    expect(registered.status()).toBe(201);
    const backend=resolve('../backend');
    const python=resolve(backend,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
    const granted=spawnSync(python,['-m','app.operations','grant-expert',alias],{cwd:backend,windowsHide:true,encoding:'utf-8',env:{...process.env,COGAI_DATA_DIR:resolve(backend,'test-results/browser-data')}});
    expect(granted.status,granted.stderr).toBe(0);
    const expertPage=await professional.newPage();
    await expertPage.goto('http://127.0.0.1:5173/');
    await expertPage.getByRole('button',{name:'Tiếp nhận hỗ trợ',exact:true}).click();
    await expect(expertPage.getByText('Tóm tắt giả lập chỉ chia sẻ cho người tiếp nhận',{exact:true})).toBeVisible();
    await expertPage.getByRole('button',{name:'Xác nhận tiếp nhận',exact:true}).click();
    await expect(expertPage.getByText('Đã có người xác nhận tiếp nhận',{exact:true})).toBeVisible();
    await page.getByRole('button',{name:'Rút yêu cầu',exact:true}).click();
    await expertPage.getByRole('button',{name:'Làm mới hàng đợi',exact:true}).click();
    await expect(expertPage.getByText('Không có yêu cầu trong quyền truy cập của bạn.',{exact:true})).toBeVisible();
    await professional.request.delete('http://127.0.0.1:5173/api/account');
    await page.request.delete('/api/session');
  } finally {await professional.close();}
});

test('late context restore does not overwrite an exercise edited by the user',async({page})=>{
  await page.request.post('/api/session',{data:{accepted:true,adult:true,persist:true}});
  let release!:()=>void;
  const delayed=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/api/chat',async route=>{
    if(route.request().method()==='GET'){
      await delayed;
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({turns:[],risk:null,step:'listen',situation:'',thought:''})});
    }else await route.continue();
  });
  await page.goto('/');
  await page.getByRole('button',{name:'Nhìn lại suy nghĩ',exact:true}).click();
  await page.getByRole('button',{name:'Dùng ví dụ',exact:true}).click();
  await expect(page.getByLabel('Chuyện gì đã xảy ra?')).toHaveValue(/tổ trưởng/);
  const restored=page.waitForResponse(r=>r.url().endsWith('/api/chat')&&r.request().method()==='GET');
  release();
  await restored;
  await expect(page.getByLabel('Chuyện gì đã xảy ra?')).toHaveValue(/tổ trưởng/);
  await expect(page.getByRole('button',{name:/Cùng nhìn lại/})).toBeEnabled();
});
