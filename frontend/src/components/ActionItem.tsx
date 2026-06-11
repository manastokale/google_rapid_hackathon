import { Check, CircleDollarSign } from 'lucide-react'
import { ActionItem as ActionItemType } from '../types'
import { StatusBadge } from './StatusBadge'

interface ActionItemProps {
  action: ActionItemType
  onAcknowledge: (id: string) => void
}

export function ActionItem({ action, onAcknowledge }: ActionItemProps) {
  return (
    <tr className="border-t border-white/5 text-sm">
      <td className="px-4 py-4 text-slate-300">{action.priority}</td>
      <td className="px-4 py-4">
        <div className="font-medium text-white">{action.description}</div>
        <div className="mt-1 text-slate-400">{action.recommended_action}</div>
      </td>
      <td className="px-4 py-4"><StatusBadge status={action.severity} /></td>
      <td className="px-4 py-4 text-right font-semibold text-white">
        <span className="inline-flex items-center justify-end gap-1">
          <CircleDollarSign className="h-4 w-4 text-emerald-300" />
          {action.dollar_impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </span>
      </td>
      <td className="px-4 py-4 text-slate-300">{action.owner}</td>
      <td className="px-4 py-4"><StatusBadge status={action.status} /></td>
      <td className="px-4 py-4 text-right">
        <button
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/10 bg-white/5 text-slate-200 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={action.status === 'acknowledged' || action.status === 'repaired'}
          onClick={() => onAcknowledge(action.id)}
          title="Acknowledge"
        >
          <Check className="h-4 w-4" />
        </button>
      </td>
    </tr>
  )
}
