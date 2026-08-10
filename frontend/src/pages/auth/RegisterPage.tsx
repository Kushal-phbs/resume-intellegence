import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { Mail, Lock, User, UserPlus } from "lucide-react";
import { useRegister } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { getApiErrorMessage } from "@/api/client";
import { ROUTES } from "@/constants/routes";

// Schema mirrors RegisterRequest exactly: 1-255 name, 8-128 password
const schema = z.object({
  full_name: z.string().min(1, "Full name is required").max(255),
  email: z.string().email("Enter a valid email"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128, "Password must be under 128 characters"),
  confirmPassword: z.string(),
}).refine((d) => d.password === d.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});
type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const register_ = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = ({ full_name, email, password }: FormValues) =>
    register_.mutate({ full_name, email, password });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-center text-xl">Create your account</CardTitle>
        <p className="mt-1 text-center text-sm text-muted-foreground">
          Start building a better resume today
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {/* Full name */}
          <div>
            <Label htmlFor="full_name">Full name</Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="full_name"
                type="text"
                autoComplete="name"
                placeholder="Alex Morgan"
                className="pl-9"
                {...register("full_name")}
              />
            </div>
            {errors.full_name && (
              <p className="mt-1 text-xs text-destructive">{errors.full_name.message}</p>
            )}
          </div>

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
                autoComplete="new-password"
                placeholder="••••••••"
                className="pl-9"
                {...register("password")}
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          {/* Confirm password */}
          <div>
            <Label htmlFor="confirmPassword">Confirm password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                placeholder="••••••••"
                className="pl-9"
                {...register("confirmPassword")}
              />
            </div>
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-destructive">{errors.confirmPassword.message}</p>
            )}
          </div>

          {/* API error */}
          {register_.isError && (
            <ErrorMessage message={getApiErrorMessage(register_.error)} />
          )}

          <Button type="submit" className="w-full" isLoading={register_.isPending}>
            <UserPlus className="h-4 w-4" />
            Create account
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to={ROUTES.login} className="font-semibold text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
