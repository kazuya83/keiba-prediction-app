/**
 * 登録フォームコンポーネント。
 * パスワード強度表示を含む。
 */

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { Button } from "../../components/common/Button";
import { useRegister } from "../../lib/api/auth";
import { useAuthStore } from "../../stores";
import { registerSchema, getPasswordStrength, type RegisterFormData } from "./schemas";

export function RegisterForm() {
  const navigate = useNavigate();
  const registerMutation = useRegister();
  const { setTokens } = useAuthStore();
  const [password, setPassword] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const watchedPassword = watch("password", "");

  const onSubmit = async (data: RegisterFormData) => {
    try {
      const token = await registerMutation.mutateAsync({
        email: data.email,
        password: data.password,
      });
      setTokens(token);
      navigate("/dashboard");
    } catch (error) {
      // エラーはReact Queryが処理する
      console.error("登録に失敗しました:", error);
    }
  };

  const passwordStrength = watchedPassword ? getPasswordStrength(watchedPassword) : null;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          メールアドレス
        </label>
        <input
          id="email"
          type="email"
          {...register("email")}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          placeholder="example@example.com"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
          パスワード
        </label>
        <input
          id="password"
          type="password"
          {...register("password")}
          onChange={(e) => {
            setPassword(e.target.value);
            register("password").onChange(e);
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          placeholder="8文字以上、大文字・小文字・数字を含む"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
        {passwordStrength && watchedPassword && (
          <div className="mt-2">
            <div className="flex items-center gap-2 mb-1">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${passwordStrength.color}`}
                  style={{ width: `${(passwordStrength.score / 6) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">{passwordStrength.label}</span>
            </div>
          </div>
        )}
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
          パスワード（確認）
        </label>
        <input
          id="confirmPassword"
          type="password"
          {...register("confirmPassword")}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          placeholder="パスワードを再入力"
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
        )}
      </div>

      {registerMutation.isError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-800">
            {registerMutation.error instanceof Error
              ? registerMutation.error.message
              : "登録に失敗しました。メールアドレスが既に使用されている可能性があります。"}
          </p>
        </div>
      )}

      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? "登録中..." : "登録"}
      </Button>
    </form>
  );
}

