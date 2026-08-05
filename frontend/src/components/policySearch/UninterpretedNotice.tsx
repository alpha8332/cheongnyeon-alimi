import './PolicySearchSidebar.css';

interface UninterpretedNoticeProps {
  notices: string[];
}

export default function UninterpretedNotice({ notices }: UninterpretedNoticeProps) {
  if (notices.length === 0) {
    return null;
  }

  return (
    <div className="policy-search-uninterpreted" role="note">
      {notices.map((notice) => (
        <p key={notice}>{notice}</p>
      ))}
    </div>
  );
}
