import { Link } from 'react-router-dom';
import Card from '@/components/common/Card';
import PartialBadge from '@/components/policy/PartialBadge';
import type { NormalizedProgram } from '@/types/policy';
import {
  formatCategoryTags,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';
import { encodeProgramRouteId } from '@/utils/programId';

interface PolicyCardProps {
  program: NormalizedProgram;
}

export default function PolicyCard({ program }: PolicyCardProps) {
  const categoryTags = formatCategoryTags(program);

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
            <Link to={`/programs/${encodeProgramRouteId(program)}`}>
              {program.title}
            </Link>
            <PartialBadge program={program} />
          </h4>
          <p style={{ margin: '8px 0 0' }}>{formatOrganization(program)}</p>
          <p style={{ margin: '4px 0 0' }}>{formatRegion(program)}</p>
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
          {getDDayLabel(program)}
        </div>
      </div>
    </Card>
  );
}
