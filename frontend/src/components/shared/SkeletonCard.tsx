const SkeletonCard = () => (
  <div className="glass-card rounded-xl p-6 space-y-4 animate-pulse">
    <div className="h-4 bg-muted rounded w-1/3" />
    <div className="space-y-2">
      <div className="h-3 bg-muted rounded w-full" />
      <div className="h-3 bg-muted rounded w-5/6" />
      <div className="h-3 bg-muted rounded w-2/3" />
    </div>
    <div className="flex gap-2">
      <div className="h-6 bg-muted rounded-full w-16" />
      <div className="h-6 bg-muted rounded-full w-20" />
      <div className="h-6 bg-muted rounded-full w-14" />
    </div>
  </div>
);

export default SkeletonCard;
