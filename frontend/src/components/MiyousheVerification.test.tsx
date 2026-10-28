import {renderToStaticMarkup} from 'react-dom/server';
import {describe,expect,it} from 'vitest';
import MiyousheVerification from './MiyousheVerification';

describe('record verification in a native modal',()=>{
  it('provides a local challenge host within each verification view',()=>{
    const verification={verification_id:'a'.repeat(43),expires_at:'2099-01-01T00:00:00Z'};
    const props={verification,onSuccess:()=>undefined,onCancel:()=>undefined,onBusyChange:()=>undefined};
    const html=renderToStaticMarkup(<div role="dialog"><MiyousheVerification {...props}/><MiyousheVerification {...props}/></div>);
    const hosts=[...html.matchAll(/<div id="([^"]+)" class="miyoushe-verification-area"/g)].map(match=>match[1]);
    expect(hosts).toHaveLength(2);
    expect(new Set(hosts).size).toBe(2);
    expect(hosts.every(id=>/^[a-zA-Z0-9_-]+$/.test(id))).toBe(true);
    expect(html.indexOf('miyoushe-verification-area')).toBeLessThan(html.indexOf('完成安全验证并继续获取'));
    expect(html).not.toContain(verification.verification_id);
  });
});
