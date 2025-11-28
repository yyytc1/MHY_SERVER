const TARGET = 'https://user.mihoyo.com/';

document.getElementById('submit').addEventListener('click', async () => {
  const token = document.getElementById('token').value.trim();
  if (!token) return;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const gotoSteam = !tab.url.startsWith(TARGET);

  if (gotoSteam) {
    await chrome.tabs.update(tab.id, { url: TARGET });
    await new Promise(r => {
      const onUp = (id, info) => {
        if (id === tab.id && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(onUp);
          r();
        }
      };
      chrome.tabs.onUpdated.addListener(onUp);
    });
  }

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: setCookie,
    args: [token]
  });

  window.close();
});

function setCookie(raw) {
  const [account_id_v2, account_mid_v2, cookie_token_v2] = raw.split('|');

	// 生成目标结构
	const cookies = [
	  {
	    name: 'cookie_token_v2',
	    value: cookie_token_v2,
	    domain: '.mihoyo.com',
	    path: '/',
	    httpOnly: true,
	    secure: true
	  },
	  {
	    name: 'account_mid_v2',
	    value: account_mid_v2,
	    domain: '.mihoyo.com',
	    path: '/',
	    secure: true
	  },
	  {
	    name: 'account_id_v2',
	    value: account_id_v2,
	    domain: '.mihoyo.com',
	    path: '/',
	    secure: true
	  }
	];
	cookies.forEach(c => {
	  document.cookie = `${c.name}=${c.value}; path=${c.path}; domain=${c.domain}${c.secure ? '; secure' : ''}`;
	});
	window.location.href = 'https://user.mihoyo.com/';
}