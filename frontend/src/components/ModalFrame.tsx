import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

type Props = { title:string; subtitle?:string; drawer?:boolean; wide?:boolean; children:ReactNode; footer?:ReactNode; onClose:()=>void };

/** Native dialogs provide modal focus, Escape handling and an inert background. */
export default function ModalFrame({title,subtitle,drawer,wide,children,footer,onClose}:Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  const titleId = useId();
  useEffect(() => {
    const node = dialog.current;
    const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    node?.showModal();
    return () => {
      node?.close();
      document.body.style.overflow = overflow;
      if (trigger?.isConnected && trigger.getClientRects().length) trigger.focus();
    };
  }, []);
  return createPortal(<dialog ref={dialog} className={`workbench-dialog ${drawer?'workbench-drawer':''} ${wide?'workbench-dialog-wide':''}`}
    aria-labelledby={titleId} onCancel={event=>{event.preventDefault();close.current();}}
    onClick={event=>{if(event.target===event.currentTarget){const rect=event.currentTarget.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)close.current();}}}>
    <header className="dialog-heading"><div><p className="eyebrow">COMBAT LAB / DETAILS</p><h2 id={titleId}>{title}</h2>{subtitle&&<p>{subtitle}</p>}</div><button type="button" className="icon-button" aria-label={`关闭${title}`} onClick={onClose}>×</button></header>
    <div className="dialog-body">{children}</div>
    {footer&&<footer className="dialog-footer">{footer}</footer>}
  </dialog>,document.body);
}
