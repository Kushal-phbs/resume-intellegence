import { User, Mail, Shield, Calendar, Clock, Info } from "lucide-react";
import { useCurrentUser } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { formatDate } from "@/lib/utils";

function ProfileSkeleton() {
  return (
    <div className="max-w-xl space-y-6">
      <Skeleton className="h-8 w-40" />
      <div className="flex items-center gap-5">
        <Skeleton className="h-20 w-20 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-36" />
        </div>
      </div>
      <Skeleton className="h-40 w-full" />
    </div>
  );
}

export function ProfilePage() {
  const { data: user, isLoading, isError, error, refetch } = useCurrentUser();

  if (isLoading) return <ProfileSkeleton />;
  if (isError || !user) return (
    <div className="max-w-xl">
      <ErrorState error={error} onRetry={() => refetch()} />
    </div>
  );

  const initials = user.full_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="mt-1 text-sm text-muted-foreground">Your account information.</p>
      </div>

      {/* Avatar + name hero */}
      <div className="flex items-center gap-5">
        <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-primary/15 text-2xl font-bold text-primary">
          {initials}
        </div>
        <div>
          <p className="text-xl font-bold">{user.full_name}</p>
          <p className="text-sm text-muted-foreground">{user.email}</p>
          <div className="mt-1.5 flex gap-2">
            <Badge variant={user.role === "admin" ? "destructive" : "default"}>
              <Shield className="h-3 w-3" />
              {user.role}
            </Badge>
            <Badge variant={user.is_active ? "success" : "muted"}>
              {user.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        </div>
      </div>

      {/* Account details */}
      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <User className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Full name</p>
              <p className="text-sm font-medium">{user.full_name}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Mail className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Email address</p>
              <p className="text-sm font-medium">{user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Shield className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Role</p>
              <p className="text-sm font-medium capitalize">{user.role}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Calendar className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Member since</p>
              <p className="text-sm font-medium">{formatDate(user.created_at)}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Clock className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Last updated</p>
              <p className="text-sm font-medium">{formatDate(user.updated_at)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Backend limitation notice */}
      <div className="flex items-start gap-2 rounded-md border border-border bg-muted/40 px-4 py-3 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>
          Profile editing is not available — the backend only exposes a read-only{" "}
          <code className="rounded bg-muted px-1">GET /users/me</code> endpoint. To update
          your name or email, contact your administrator.
        </span>
      </div>
    </div>
  );
}
