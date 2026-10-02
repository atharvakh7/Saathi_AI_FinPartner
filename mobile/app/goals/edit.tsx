/** S19 Edit Goal (`?id=`): loads the goal, then the shared form. */
import { router, useLocalSearchParams } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { getGoal } from '@/api/endpoints';
import { EmptyState, ErrorBanner, Screen, SkeletonCard } from '@/components';
import { GoalForm } from '@/features/goals/GoalForm';
import { goalKeys } from '@/features/goals/goals';

export default function EditGoal() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const goal = useQuery({ queryKey: goalKeys.detail(id ?? ''), queryFn: () => getGoal(id!), enabled: !!id });
  if (goal.data) return <GoalForm key={goal.data.id} existing={goal.data} />;
  return (
    <Screen title={t('goals.editTitle')} back>
      {goal.isPending && id ? <SkeletonCard lines={4} /> : null}
      {goal.error ? <ErrorBanner error={goal.error} onRetry={() => void goal.refetch()} /> : null}
      {!id ? <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')} onAction={() => router.back()} /> : null}
    </Screen>
  );
}
