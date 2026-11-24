"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ServiceForm } from "@/components/ServiceForm";
import { ApiError, api } from "@/lib/api";

export default function NewServicePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  return (
    <div>
      <h1 className="mb-6 font-serif text-3xl">Add service</h1>
      <ServiceForm
        submitLabel="Create service"
        pending={pending}
        error={error}
        onSubmit={async (body) => {
          setPending(true);
          setError("");
          try {
            await api.createService(body);
            await queryClient.invalidateQueries();
            router.push("/admin/services");
          } catch (caught) {
            setError(caught instanceof ApiError ? caught.message : "Could not create the service");
          } finally {
            setPending(false);
          }
        }}
      />
    </div>
  );
}
