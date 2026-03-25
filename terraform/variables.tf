variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "server_type" {
  description = "Hetzner Cloud server type"
  type        = string
  default     = "cpx41"
}

variable "server_name" {
  description = "Name for the VPS instance"
  type        = string
  default     = "isnad-graph-prod"
}

variable "datacenter" {
  description = "Hetzner Cloud datacenter"
  type        = string
  default     = "ash-dc1"
}
