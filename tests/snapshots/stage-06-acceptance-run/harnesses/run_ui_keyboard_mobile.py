import run_ui_acceptance as b
from run_ui_acceptance import *
def mobile(e,o):
 p=e.page;p.set_viewport_size({'width':390,'height':844});o['keys']=[];o['trees']=[]
 def reach(sel):
  for _ in range(120):
   if p.locator(sel).evaluate('(e)=>e===document.activeElement'):
    o['keys'].append({'target':sel,'outline':p.locator(sel).evaluate('(e)=>getComputedStyle(e).outline')});return
   p.keyboard.press('Tab')
  raise AssertionError('Tab target unreachable '+sel)
 reach('#login-form [name=email]');p.keyboard.type('admin@meetspace.test');reach('#login-form [name=password]');p.keyboard.type('MeetSpace!2026');p.keyboard.press('Enter');p.locator('#filter-date').wait_for();reach('#filter-capacity');p.keyboard.press('ArrowDown');p.keyboard.press('Enter');reach('#filter-equipment');p.keyboard.press('ArrowDown');p.keyboard.press('Enter');reach('[data-book-room="1"]');p.keyboard.press('Enter');reach('#booking-form [name=title]');p.keyboard.type('手机键盘预约');o['trees'].append(p.locator('#booking-dialog').aria_snapshot());reach('#booking-form [type=submit]');p.keyboard.press('Enter');p.locator('#booking-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');reach('nav [data-page=bookings]');p.keyboard.press('Enter');p.locator('[aria-label="取消手机键盘预约"]').first.wait_for();reach('[aria-label="取消手机键盘预约"]');p.keyboard.press('Enter');o['trees'].append(p.locator('#confirm-dialog').aria_snapshot());p.keyboard.press('Escape');assert p.locator('[aria-label="取消手机键盘预约"]').evaluate('(e)=>e===document.activeElement');p.keyboard.press('Enter');reach('#confirm-cancel');p.keyboard.press('Enter');p.locator('#confirm-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');reach('nav [data-page=inbox]');p.keyboard.press('Enter');p.locator('#mark-read').wait_for();reach('#mark-read');p.keyboard.press('Enter');p.wait_for_function('() => !state.loading && !document.querySelector(".nav-badge")');o['trees'].append(p.locator('body').aria_snapshot());o['shot']=e.shot('keyboard-mobile-complete')
if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=910
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True);group('mobile-keyboard-complete-path',['AI-interface-experience-13','AI-WB-ui-accessibility-focus'],mobile);b.browser.close()
