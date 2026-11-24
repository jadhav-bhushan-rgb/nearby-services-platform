"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ServiceForm } from "@/components/ServiceForm";
import { ApiError, api } from "@/lib/api";

export default function EditServicePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const query = useQuery({ queryKey: ["service", params.id], queryFn: () => api.service(params.id) });

  return (
    <div>
      <h1 className="mb-6 font-serif text-3xl">Edit service</h1>
      {query.isLoading ? <p className="text-sm">Loading service</p> : null}
      {query.isError ? <p className="text-sm text-clay">This service could not be loaded.</p> : null}
      {query.data ? (
        <ServiceForm
          initial={query.data}
          submitLabel="Save changes"
          pending={pending}
          error={error}
          onSubmit={async (body) => {
            setPending(true);
            setError("");
            try {
              await api.updateService(params.id, body);
              await queryClient.invalidateQueries();
              router.push("/admin/services");
            } catch (caught) {
              setError(caught instanceof ApiError ? caught.message : "Could not save the service");
            } finally {
              setPending(false);
            }
          }}
        />
      ) : null}
    </div>
  );
}
