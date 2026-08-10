import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { Mail, Lock, LogIn } from "lucide-react";
import { useLogin } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { getApiErrorMessage } from "@/api/client";
import { ROUTES } from "@/constants/routes";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (values: FormValues) => login.mutate(values);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-center text-xl">Welcome back</CardTitle>
        <p className="mt-1 text-center text-sm text-muted-foreground">
          Sign in to Resume Intelligence
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {/* Email */}
          <div>
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                className="pl-9"
                {...register("email")}
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                className="pl-9"
                {...register("password")}
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          {/* API error */}
          {login.isError && (
            <ErrorMessage message={getApiErrorMessage(login.error)} />
          )}

          <Button
            type="submit"
            className="w-full"
            isLoading={login.isPending}
          >
            <LogIn className="h-4 w-4" />
            Sign in
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Don't have an account?{" "}
          <Link to={ROUTES.register} className="font-semibold text-primary hover:underline">
            Create one
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
