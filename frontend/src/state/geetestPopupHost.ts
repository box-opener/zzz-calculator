/**
 * GeeTest v3 can still append its bind popup to body despite an `area` option.
 * A body popup sits below native showModal() dialogs and is inert there.
 * Move only newly created SDK popup roots into the verification view, keeping
 * the SDK's own element references, handlers and close/destroy lifecycle.
 */
export function hostGeetestPopups(host:HTMLElement):()=>void {
  const body=host.ownerDocument.body;
  const previous=new Set(body.children);
  const adopted=new Set<Element>();
  const movePopups=()=>{
    for(const node of Array.from(body.children)){
      if(!previous.has(node)&&node.classList.contains('geetest_panel')){
        adopted.add(node);
        host.appendChild(node);
      }
    }
  };
  const observer=new MutationObserver(movePopups);
  observer.observe(body,{childList:true});
  return ()=>{
    observer.disconnect();
    for(const node of adopted)node.remove();
  };
}
