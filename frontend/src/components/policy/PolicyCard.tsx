import { Link } from 'react-router-dom';
import Card from '@/components/common/Card';
import PartialBadge from '@/components/policy/PartialBadge';
import type { PolicyDto } from '@/types/policy';
import {
  formatCategoryTags,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';

interface PolicyCardProps {
  policy: PolicyDto;
}

export default function PolicyCard({ policy }: PolicyCardProps) {
  const categoryTags = formatCategoryTags(policy);
  const detailPath =
    policy.data_quality_status === 'partial'
      ? `/programs/${policy.id}?include_partial=true`
      : `/programs/${policy.id}`;

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <h4
            style={{
              margin: 0,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            <Link to={detailPath}>
              {policy.title}
            </Link>
            <PartialBadge policy={policy} />
          </h4>
          <p style={{ margin: '8px 0 0' }}>{formatOrganization(policy)}</p>
          <p style={{ margin: '4px 0 0' }}>{formatRegion(policy)}</p>
          <div style={{ marginTop: '8px' }}>
            {categoryTags.map((tag) => (
              <span
                key={tag}
                style={{
                  border: '1px solid black',
                  padding: '2px 6px',
                  marginRight: '6px',
                  fontSize: '12px',
                  display: 'inline-block',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div
          style={{
            border: '1px solid black',
            padding: '8px',
            minWidth: '72px',
            textAlign: 'center',
            alignSelf: 'flex-start',
          }}
        >
          {getDDayLabel(policy)}
        </div>
      </div>
    </Card>
  );
}
